from os import path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from cantusdata.models import Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus

MEI_FIXTURE = path.join(
    settings.TEST_MEI_FILES_PATH, "123723", "cdn-hsmu-m2149l4_001r.mei"
)
URL = "/api/mei-submissions/"


class MEISubmissionViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        with open(MEI_FIXTURE, encoding="utf-8") as mei_file:
            cls.mei = mei_file.read()

        cls.manuscript = Manuscript.objects.create(
            id=123723, name="Test manuscript", siglum="CDN-Hsmu M2149.L4"
        )
        cls.mapped_folio = Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=cls.manuscript
        )
        cls.unmapped_folio = Folio.objects.create(
            number="002r", image_uri="", manuscript=cls.manuscript
        )

        user_model = get_user_model()
        cls.depositor = user_model.objects.create(username="mothra")
        cls.depositor.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="cantusdata",
                codename__in=["add_meisubmission", "view_meisubmission"],
            )
        )
        cls.depositor_token = Token.objects.create(user=cls.depositor)

        cls.outsider = user_model.objects.create(username="outsider")
        cls.outsider_token = Token.objects.create(user=cls.outsider)

    def authenticate(self, token: Token) -> None:
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def payload(self, **overrides: object) -> dict:
        body = {
            "manuscript_id": self.manuscript.pk,
            "folio_number": "001r",
            "mei": self.mei,
            "submitter": "asadra",
            "comment": "corrected in Neon",
        }
        body.update(overrides)
        return body

    # --- authentication and permissions ---------------------------------

    def test_anonymous_post_is_rejected(self) -> None:
        response = self.client.post(URL, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(MEISubmission.objects.count(), 0)

    def test_token_without_permission_is_rejected(self) -> None:
        self.authenticate(self.outsider_token)
        response = self.client.post(URL, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MEISubmission.objects.count(), 0)

    def test_anonymous_get_is_rejected(self) -> None:
        response = self.client.get(URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- the happy path -------------------------------------------------

    def test_deposit_creates_a_pending_submission(self) -> None:
        self.authenticate(self.depositor_token)
        response = self.client.post(URL, self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["status"], SubmissionStatus.PENDING)

        submission = MEISubmission.objects.get(pk=response.data["id"])
        self.assertEqual(submission.manuscript_id, self.manuscript.pk)
        self.assertEqual(submission.folio, self.mapped_folio)
        self.assertEqual(submission.folio_number, "001r")
        self.assertEqual(submission.submitter, "asadra")
        self.assertEqual(submission.comment, "corrected in Neon")
        self.assertEqual(submission.mei, self.mei)
        self.assertEqual(submission.published_path, "")

    def test_response_does_not_include_the_mei_body(self) -> None:
        self.authenticate(self.depositor_token)
        response = self.client.post(URL, self.payload(), format="json")
        self.assertNotIn("mei", response.data)

    def test_folio_number_is_canonicalized(self) -> None:
        """A submitter sending "1r" gets the manuscript's own "001r" stored."""
        self.authenticate(self.depositor_token)
        response = self.client.post(URL, self.payload(folio_number="1r"), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        submission = MEISubmission.objects.get(pk=response.data["id"])
        self.assertEqual(submission.folio_number, "001r")
        self.assertEqual(submission.folio, self.mapped_folio)

    # --- validation -----------------------------------------------------

    def test_unknown_manuscript_is_rejected(self) -> None:
        self.authenticate(self.depositor_token)
        response = self.client.post(
            URL, self.payload(manuscript_id=999999), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("manuscript_id", response.data)

    def test_unknown_folio_is_rejected_without_creating_one(self) -> None:
        self.authenticate(self.depositor_token)
        folios_before = Folio.objects.count()
        response = self.client.post(
            URL, self.payload(folio_number="999r"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("folio_number", response.data)
        self.assertEqual(Folio.objects.count(), folios_before)

    def test_folio_number_is_not_treated_as_a_pattern(self) -> None:
        """
        Folio numbers are matched with a regex to be forgiving about leading
        zeros, so a submitted value must not be able to act as one and resolve to
        a folio the submitter did not name.
        """
        self.authenticate(self.depositor_token)
        for pattern in (".*", "00.r", "[0-9]+r"):
            with self.subTest(pattern=pattern):
                response = self.client.post(
                    URL, self.payload(folio_number=pattern), format="json"
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST, response.data
                )
                self.assertIn("folio_number", response.data)
        self.assertEqual(MEISubmission.objects.count(), 0)

    def test_unmapped_folio_is_rejected(self) -> None:
        """
        A folio with no image_uri would index n-grams that cannot be located on
        the page, and index_manuscript_mei cannot tell that case from a missing
        folio, so it is refused here instead.
        """
        self.authenticate(self.depositor_token)
        response = self.client.post(
            URL, self.payload(folio_number="002r"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("folio_number", response.data)
        self.assertIn("not mapped", str(response.data["folio_number"]))

    def test_malformed_xml_is_rejected(self) -> None:
        self.authenticate(self.depositor_token)
        response = self.client.post(
            URL, self.payload(mei="<mei><unclosed>"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mei", response.data)

    def test_mei_without_neumes_is_rejected(self) -> None:
        self.authenticate(self.depositor_token)
        response = self.client.post(
            URL,
            self.payload(mei='<?xml version="1.0"?><mei><music/></mei>'),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mei", response.data)

    def test_oversized_mei_is_rejected(self) -> None:
        self.authenticate(self.depositor_token)
        response = self.client.post(
            URL, self.payload(mei="x" * (5 * 1024 * 1024 + 1)), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mei", response.data)

    # --- resubmission ---------------------------------------------------

    def test_identical_resubmission_returns_the_existing_review(self) -> None:
        self.authenticate(self.depositor_token)
        first = self.client.post(URL, self.payload(), format="json")
        second = self.client.post(URL, self.payload(), format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["id"], first.data["id"])
        self.assertEqual(MEISubmission.objects.count(), 1)

    def test_new_content_supersedes_the_earlier_pending_submission(self) -> None:
        self.authenticate(self.depositor_token)
        first = self.client.post(URL, self.payload(), format="json")
        corrected = self.mei.replace("</mei>", "<!-- corrected --></mei>")
        second = self.client.post(URL, self.payload(mei=corrected), format="json")
        self.assertEqual(second.status_code, status.HTTP_201_CREATED, second.data)

        self.assertEqual(
            MEISubmission.objects.get(pk=first.data["id"]).status,
            SubmissionStatus.SUPERSEDED,
        )
        self.assertEqual(
            MEISubmission.objects.get(pk=second.data["id"]).status,
            SubmissionStatus.PENDING,
        )
        self.assertEqual(
            MEISubmission.objects.filter(status=SubmissionStatus.PENDING).count(), 1
        )

    # --- status list ----------------------------------------------------

    def test_list_is_filtered_by_submitter(self) -> None:
        self.authenticate(self.depositor_token)
        self.client.post(URL, self.payload(), format="json")
        self.client.post(
            URL,
            self.payload(submitter="someone-else", folio_number="1r"),
            format="json",
        )

        response = self.client.get(URL, {"submitter": "asadra"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["submitter"], "asadra")
        self.assertIn("review_note", response.data[0])
        self.assertNotIn("mei", response.data[0])
