from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cantusdata.models import Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus

PUBLISH_TASK = "cantusdata.admin.admin.publish_mei_submission_task"


class MEISubmissionAdminTestCase(TestCase):
    """
    The review flow. Publishing needs no explanation and so is available as a
    bulk action; asking for a correction or refusing has to tell the submitter
    why, and so goes through the change form where there is a field for it.
    """

    fixtures = ["1_users"]

    def setUp(self) -> None:
        self.client.login(username="ahankins", password="hahaha")
        self.manuscript = Manuscript.objects.create(
            id=123723, siglum="CDN-Hsmu M2149.L4"
        )
        self.folio = Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=self.manuscript
        )
        self.submission = MEISubmission.objects.create(
            manuscript=self.manuscript,
            folio=self.folio,
            folio_number="001r",
            mei="<mei>notation</mei>",
            submitter="asadra",
        )

    @property
    def change_url(self) -> str:
        return reverse(
            "admin:cantusdata_meisubmission_change", args=[self.submission.pk]
        )

    @property
    def download_url(self) -> str:
        return reverse("admin:cantusdata_meisubmission_mei", args=[self.submission.pk])

    def review(self, **fields: str) -> object:
        return self.client.post(self.change_url, fields)

    # --- the change form ------------------------------------------------

    def test_refusing_without_a_reason_is_refused(self) -> None:
        response = self.review(status=SubmissionStatus.REFUSED, review_note="")
        self.assertEqual(response.status_code, 200)  # redisplayed with errors
        self.assertContains(response, "Say why")
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, SubmissionStatus.PENDING)

    def test_refusing_with_a_reason_is_recorded(self) -> None:
        response = self.review(
            status=SubmissionStatus.REFUSED, review_note="Wrong folio."
        )
        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, SubmissionStatus.REFUSED)
        self.assertEqual(self.submission.review_note, "Wrong folio.")
        self.assertIsNotNone(self.submission.reviewed_at)
        self.assertEqual(self.submission.reviewed_by.username, "ahankins")

    def test_requesting_a_correction_needs_a_reason_too(self) -> None:
        response = self.review(
            status=SubmissionStatus.CORRECTION_REQUESTED, review_note="  "
        )
        self.assertEqual(response.status_code, 200)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, SubmissionStatus.PENDING)

    def test_publishing_from_the_form_queues_the_task_and_waits(self) -> None:
        """
        The row only reads PUBLISHED once the folio really is indexed, so the
        form leaves the status alone and the task flips it.
        """
        with patch(PUBLISH_TASK) as task:
            response = self.review(status=SubmissionStatus.PUBLISHED, review_note="")
        self.assertEqual(response.status_code, 302)
        task.apply_async.assert_called_once()
        kwargs = task.apply_async.call_args.kwargs["kwargs"]
        self.assertEqual(kwargs["submission_id"], self.submission.pk)
        # Read by NewTaskResultAdmin to label the task row.
        self.assertEqual(kwargs["manuscript_ids"], [self.manuscript.pk])

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, SubmissionStatus.PENDING)
        self.assertIsNotNone(self.submission.reviewed_at)

    def test_a_reviewed_submission_cannot_be_reviewed_again(self) -> None:
        self.submission.status = SubmissionStatus.REFUSED
        self.submission.save()
        with patch(PUBLISH_TASK) as task:
            self.review(status=SubmissionStatus.PUBLISHED, review_note="")
        task.apply_async.assert_not_called()
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, SubmissionStatus.REFUSED)

    def test_submissions_cannot_be_hand_entered(self) -> None:
        response = self.client.get(reverse("admin:cantusdata_meisubmission_add"))
        self.assertEqual(response.status_code, 403)

    # --- the bulk action ------------------------------------------------

    def test_publish_action_queues_one_task_per_submission(self) -> None:
        other = MEISubmission.objects.create(
            manuscript=self.manuscript,
            folio=self.folio,
            folio_number="001v",
            mei="<mei>more</mei>",
            submitter="asadra",
        )
        with patch(PUBLISH_TASK) as task:
            response = self.client.post(
                reverse("admin:cantusdata_meisubmission_changelist"),
                {
                    "action": "publish_submissions",
                    "_selected_action": [self.submission.pk, other.pk],
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.apply_async.call_count, 2)

    def test_publish_action_skips_already_reviewed_submissions(self) -> None:
        self.submission.status = SubmissionStatus.PUBLISHED
        self.submission.save()
        with patch(PUBLISH_TASK) as task:
            response = self.client.post(
                reverse("admin:cantusdata_meisubmission_changelist"),
                {
                    "action": "publish_submissions",
                    "_selected_action": [self.submission.pk],
                },
                follow=True,
            )
        task.apply_async.assert_not_called()
        self.assertContains(response, "already been reviewed")

    # --- the MEI itself -------------------------------------------------

    def test_mei_can_be_downloaded(self) -> None:
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn("cdn-hsmu-m2149l4_001r.mei", response["Content-Disposition"])
        self.assertEqual(response.content.decode(), "<mei>notation</mei>")

    def test_the_change_form_offers_the_download(self) -> None:
        """
        The endpoint above being reachable is not enough: the reviewer can only
        use it if the change form actually renders a link to it. It did not --
        the size was interpolated with a "{:.1f}" placeholder, which format_html
        cannot apply to the string it escapes its arguments into, and the
        ValueError that raised made the admin render the whole field as its
        empty-value dash instead.
        """
        response = self.client.get(self.change_url)
        self.assertContains(response, self.download_url)
        self.assertContains(response, "cdn-hsmu-m2149l4_001r.mei")
        # 18 bytes of "<mei>notation</mei>"... the point is a number, not a dash.
        self.assertContains(response, "0.0 KB")

    def test_the_changelist_offers_the_download_too(self) -> None:
        """A reviewer working a batch should not have to open each row first."""
        response = self.client.get(reverse("admin:cantusdata_meisubmission_changelist"))
        self.assertContains(response, self.download_url)

    def test_downloading_a_submission_that_is_gone_is_a_404(self) -> None:
        missing = reverse(
            "admin:cantusdata_meisubmission_mei", args=[self.submission.pk]
        )
        self.submission.delete()
        self.assertEqual(self.client.get(missing).status_code, 404)

    def test_staff_without_view_permission_cannot_download(self) -> None:
        """
        admin_view() only establishes that the caller is staff, which is not the
        same as being allowed to read this model.
        """
        outsider = User.objects.create_user(
            username="outsider", password="hahaha", is_staff=True
        )
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(self.download_url).status_code, 403)
