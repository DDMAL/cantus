from django.test import TestCase

from cantusdata.models import Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus


class MEISubmissionModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.manuscript = Manuscript.objects.create(
            id=555, name="Test manuscript", siglum="CDN-Hsmu M2149.L4"
        )
        cls.folio = Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=cls.manuscript
        )

    def make_submission(self, **kwargs: object) -> MEISubmission:
        defaults = {
            "manuscript": self.manuscript,
            "folio": self.folio,
            "folio_number": "001r",
            "mei": "<mei/>",
            "submitter": "someone",
        }
        defaults.update(kwargs)
        return MEISubmission.objects.create(**defaults)  # type: ignore[arg-type]

    def test_content_hash_is_computed_on_save(self) -> None:
        submission = self.make_submission()
        self.assertEqual(submission.content_sha256, MEISubmission.hash_mei("<mei/>"))
        self.assertEqual(len(submission.content_sha256), 64)

    def test_identical_content_hashes_identically(self) -> None:
        self.assertEqual(
            MEISubmission.hash_mei("<mei>a</mei>"),
            MEISubmission.hash_mei("<mei>a</mei>"),
        )
        self.assertNotEqual(
            MEISubmission.hash_mei("<mei>a</mei>"),
            MEISubmission.hash_mei("<mei>b</mei>"),
        )

    def test_mei_filename_uses_slugified_siglum(self) -> None:
        submission = self.make_submission()
        self.assertEqual(submission.mei_filename, "cdn-hsmu-m2149l4_001r.mei")

    def test_mei_filename_falls_back_to_manuscript_id(self) -> None:
        manuscript = Manuscript.objects.create(id=556, siglum=None)
        submission = self.make_submission(manuscript=manuscript, folio=None)
        self.assertEqual(submission.mei_filename, "ms556_001r.mei")

    def test_mei_filename_folio_is_the_last_underscore_segment(self) -> None:
        """The indexer parses the folio from after the last underscore."""
        submission = self.make_submission()
        parsed = submission.mei_filename.split("_")[-1].split(".")[0]
        self.assertEqual(parsed, "001r")

    def test_only_pending_submissions_can_be_reviewed(self) -> None:
        submission = self.make_submission()
        for outcome in (
            SubmissionStatus.PUBLISHED,
            SubmissionStatus.CORRECTION_REQUESTED,
            SubmissionStatus.REFUSED,
        ):
            with self.subTest(outcome=outcome):
                self.assertTrue(submission.can_transition_to(outcome))
        with self.subTest("superseded is not a review outcome"):
            self.assertFalse(submission.can_transition_to(SubmissionStatus.SUPERSEDED))
        submission.status = SubmissionStatus.REFUSED
        with self.subTest("a reviewed submission cannot be reviewed again"):
            self.assertFalse(submission.can_transition_to(SubmissionStatus.PUBLISHED))

    def test_folio_deletion_keeps_the_submission(self) -> None:
        """
        Chant re-import deletes and recreates folios; review history must survive
        that, which is why folio is SET_NULL and folio_number is denormalized.
        """
        submission = self.make_submission()
        self.folio.delete()
        submission.refresh_from_db()
        self.assertIsNone(submission.folio)
        self.assertEqual(submission.folio_number, "001r")
