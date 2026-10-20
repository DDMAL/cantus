from os import path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from cantusdata.metrics.celery_signals import PUBLISHED_AT_HEADER, stamp_publish_time
from cantusdata.models import Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus
from cantusdata.tasks import publish_mei_submission_task

from .utils import sample

MEI_FIXTURE = path.join(
    settings.TEST_MEI_FILES_PATH, "123723", "cdn-hsmu-m2149l4_001r.mei"
)
PUBLISH_TASK = "cantusdata.admin.admin.publish_mei_submission_task"


class MEIDepositMetricsTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        with open(MEI_FIXTURE, encoding="utf-8") as mei_file:
            cls.mei = mei_file.read()
        cls.manuscript = Manuscript.objects.create(
            id=123723, name="Test manuscript", siglum="CDN-Hsmu M2149.L4"
        )
        Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=cls.manuscript
        )
        Folio.objects.create(number="002r", image_uri="", manuscript=cls.manuscript)
        depositor = get_user_model().objects.create(username="mothra")
        depositor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="cantusdata",
                codename__in=["add_meisubmission", "view_meisubmission"],
            )
        )
        cls.token = Token.objects.create(user=depositor)

    def deposit(self, **overrides: str):  # type: ignore[no-untyped-def]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        body = {
            "manuscript_id": self.manuscript.pk,
            "folio_number": "001r",
            "mei": self.mei,
            "submitter": "asadra",
        }
        body.update(overrides)
        return self.client.post("/api/mei-submissions/", body, format="json")

    def received(self, outcome: str, reason: str = "none") -> float:
        return sample(
            "cantus_mei_submissions_received_total",
            outcome=outcome,
            reason=reason,
            account="mothra",
        )

    def test_created_duplicate_and_invalid_deposits_are_told_apart(self) -> None:
        created, duplicate = self.received("created"), self.received("duplicate")
        invalid = self.received("invalid", "folio_number")
        sizes = sample("cantus_mei_submission_size_bytes_count")

        self.assertEqual(self.deposit().status_code, 201)
        self.assertEqual(self.deposit().status_code, 200)
        # An unmapped folio is refused with an error on folio_number.
        self.assertEqual(self.deposit(folio_number="002r").status_code, 400)

        self.assertEqual(self.received("created"), created + 1)
        self.assertEqual(self.received("duplicate"), duplicate + 1)
        self.assertEqual(self.received("invalid", "folio_number"), invalid + 1)
        self.assertEqual(sample("cantus_mei_submission_size_bytes_count"), sizes + 3)

    def test_a_newer_deposit_supersedes_the_pending_one(self) -> None:
        before = sample("cantus_mei_submissions_superseded_total")
        self.deposit()
        self.deposit(mei=self.mei + "\n<!-- second pass -->\n")
        self.assertEqual(sample("cantus_mei_submissions_superseded_total"), before + 1)


class MEIReviewMetricsTestCase(TestCase):
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

    def test_a_refusal_is_counted_with_its_latency(self) -> None:
        reviews = sample("cantus_mei_reviews_total", action="refuse", via="form")
        latencies = sample("cantus_mei_review_latency_seconds_count", action="refuse")
        self.client.post(
            reverse("admin:cantusdata_meisubmission_change", args=[self.submission.pk]),
            {"status": SubmissionStatus.REFUSED, "review_note": "Wrong folio."},
        )
        self.assertEqual(
            sample("cantus_mei_reviews_total", action="refuse", via="form"),
            reviews + 1,
        )
        self.assertEqual(
            sample("cantus_mei_review_latency_seconds_count", action="refuse"),
            latencies + 1,
        )

    def test_bulk_publishing_is_counted(self) -> None:
        before = sample("cantus_mei_reviews_total", action="publish", via="bulk")
        with patch(PUBLISH_TASK):
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(
                    reverse("admin:cantusdata_meisubmission_changelist"),
                    {
                        "action": "publish_submissions",
                        "_selected_action": [self.submission.pk],
                    },
                )
        self.assertEqual(
            sample("cantus_mei_reviews_total", action="publish", via="bulk"),
            before + 1,
        )


class TaskMetricsTestCase(TestCase):
    def test_a_task_run_is_counted_and_timed(self) -> None:
        manuscript = Manuscript.objects.create(id=123723, siglum="X")
        folio = Folio.objects.create(
            number="001r", image_uri="f", manuscript=manuscript
        )
        # Not claimed for publication, so the task skips it straight away.
        submission = MEISubmission.objects.create(
            manuscript=manuscript,
            folio=folio,
            folio_number="001r",
            mei="<mei/>",
            submitter="asadra",
        )
        task = "publish-mei-submission"
        runs = sample("cantus_celery_task_runs_total", task=task, outcome="success")
        timed = sample("cantus_celery_task_duration_seconds_count", task=task)
        skipped = sample("cantus_mei_publish_total", outcome="skipped")

        publish_mei_submission_task.apply(
            kwargs={"manuscript_ids": [manuscript.pk], "submission_id": submission.pk}
        )

        self.assertEqual(
            sample("cantus_celery_task_runs_total", task=task, outcome="success"),
            runs + 1,
        )
        self.assertEqual(
            sample("cantus_celery_task_duration_seconds_count", task=task), timed + 1
        )
        self.assertEqual(sample("cantus_celery_tasks_in_progress", task=task), 0)
        self.assertEqual(
            sample("cantus_mei_publish_total", outcome="skipped"), skipped + 1
        )

    def test_publishing_stamps_the_message_for_queue_wait(self) -> None:
        headers: dict[str, float] = {}
        stamp_publish_time(headers=headers)
        self.assertIn(PUBLISHED_AT_HEADER, headers)


class AdminLoginMetricsTestCase(TestCase):
    def test_failed_and_successful_logins_are_counted(self) -> None:
        User.objects.create_superuser("reviewer", "r@example.org", "right-password")
        failed = sample("cantus_admin_logins_total", outcome="failure")
        succeeded = sample("cantus_admin_logins_total", outcome="success")
        self.assertFalse(self.client.login(username="reviewer", password="wrong"))
        self.assertTrue(
            self.client.login(username="reviewer", password="right-password")
        )
        self.assertEqual(
            sample("cantus_admin_logins_total", outcome="failure"), failed + 1
        )
        self.assertEqual(
            sample("cantus_admin_logins_total", outcome="success"), succeeded + 1
        )
