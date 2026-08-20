from os import listdir, makedirs, path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings
from django.test import TestCase, override_settings
from solr.core import SolrConnection  # type: ignore

from cantusdata.models import Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus
from cantusdata.models.plugin import Plugin
from cantusdata.tasks import NOTATION_SEARCH_PLUGINS, publish_mei_submission_task

MEI_FIXTURE = path.join(
    settings.TEST_MEI_FILES_PATH, "123723", "cdn-hsmu-m2149l4_001r.mei"
)


class PublishMEISubmissionTaskTestCase(TestCase):
    """
    The publish path end to end: write the MEI into the live tree, index that one
    folio, make the manuscript's notation search reachable, and only then mark the
    submission published.
    """

    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        with open(MEI_FIXTURE, encoding="utf-8") as mei_file:
            cls.mei = mei_file.read()

    def setUp(self) -> None:
        self.mei_dir = mkdtemp(prefix="mei-files-test-")
        self.manuscript = Manuscript.objects.create(
            id=123723, siglum="CDN-Hsmu M2149.L4"
        )
        self.folio = Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=self.manuscript
        )

    def tearDown(self) -> None:
        rmtree(self.mei_dir, ignore_errors=True)
        self.solr_conn.delete_query("type:omr_ngram AND manuscript_id:123723")
        self.solr_conn.commit()

    def make_submission(self, mei: str | None = None) -> MEISubmission:
        return MEISubmission.objects.create(
            manuscript=self.manuscript,
            folio=self.folio,
            folio_number="001r",
            mei=mei if mei is not None else self.mei,
            submitter="asadra",
        )

    def publish(self, submission: MEISubmission) -> None:
        with override_settings(MEI_FILES_DIR=self.mei_dir):
            result = publish_mei_submission_task.apply(
                kwargs={
                    "manuscript_ids": [submission.manuscript_id],
                    "submission_id": submission.pk,
                }
            )
        self.assertTrue(result.successful(), result.traceback)

    def indexed_count(self, folio: str = "001r") -> int:
        results = self.solr_conn.query(
            "*:*", fq=f'type:omr_ngram AND manuscript_id:123723 AND folio:"{folio}"'
        )
        return int(results.numFound)

    def test_publishing_writes_the_mei_into_the_live_tree(self) -> None:
        submission = self.make_submission()
        self.publish(submission)

        expected = path.join(self.mei_dir, "123723", "cdn-hsmu-m2149l4_001r.mei")
        self.assertTrue(path.exists(expected))
        with open(expected, encoding="utf-8") as written:
            self.assertEqual(written.read(), self.mei)

        submission.refresh_from_db()
        self.assertEqual(submission.published_path, expected)

    def test_publishing_indexes_the_folio(self) -> None:
        submission = self.make_submission()
        self.assertEqual(self.indexed_count(), 0)
        self.publish(submission)
        self.assertGreater(self.indexed_count(), 0)

    def test_publishing_marks_the_submission_published(self) -> None:
        submission = self.make_submission()
        self.publish(submission)
        submission.refresh_from_db()
        self.assertEqual(submission.status, SubmissionStatus.PUBLISHED)
        self.assertIsNotNone(submission.reviewed_at)

    def test_publishing_attaches_the_notation_search_plugins(self) -> None:
        """Without these the client renders no notation-search fields at all."""
        submission = self.make_submission()
        self.publish(submission)
        attached = set(self.manuscript.plugins.values_list("name", flat=True))
        self.assertEqual(attached, set(NOTATION_SEARCH_PLUGINS))

    def test_publishing_exposes_the_slugs_the_client_looks_for(self) -> None:
        """
        Manuscript's serializer exposes plugins by slug and OMRSearchProvider
        matches on "neume-search"/"pitch-search", so the slugs are the contract.
        """
        submission = self.make_submission()
        self.publish(submission)
        slugs = {plugin.slug for plugin in self.manuscript.plugins.all()}
        self.assertEqual(slugs, {"neume-search", "pitch-search"})

    def test_publishing_reuses_a_plugin_row_with_a_differently_spelled_name(
        self,
    ) -> None:
        """
        Deployments already carry rows whose names are the slugs themselves,
        alongside the title-cased ones. Publishing must attach the row that is
        already there rather than add a second one with the same slug.
        """
        existing = Plugin.objects.create(name="neume-search")
        submission = self.make_submission()
        self.publish(submission)

        neume_plugins = [p for p in Plugin.objects.all() if p.slug == "neume-search"]
        self.assertEqual(neume_plugins, [existing])
        self.assertIn(existing, self.manuscript.plugins.all())

    def test_publishing_is_idempotent_for_plugins(self) -> None:
        submission = self.make_submission()
        self.publish(submission)
        self.publish(submission)
        self.assertEqual(self.manuscript.plugins.count(), 2)
        self.assertEqual(Plugin.objects.count(), 2)

    def test_republishing_replaces_rather_than_duplicates(self) -> None:
        first = self.make_submission()
        self.publish(first)
        after_first = self.indexed_count()

        corrected = self.make_submission(
            mei=self.mei.replace("</mei>", "<!-- corrected --></mei>")
        )
        self.publish(corrected)
        self.assertEqual(self.indexed_count(), after_first)

    def test_publishing_reuses_the_folio_s_existing_filename(self) -> None:
        """
        The curated archive names files with its own prefix (e.g.
        "CDN-Hsmu_M2149.L4_001r.mei"). Since the indexer reads the folio from
        after the last underscore, writing a second file under a different prefix
        would give one folio two files and double its n-grams. Publishing must
        replace the file that is there.
        """
        curated_dir = path.join(self.mei_dir, "123723")
        makedirs(curated_dir, exist_ok=True)
        curated = path.join(curated_dir, "CDN-Hsmu_M2149.L4_001r.mei")
        with open(curated, "w", encoding="utf-8") as seeded:
            seeded.write("<mei>curated</mei>")

        submission = self.make_submission()
        self.publish(submission)

        self.assertEqual(listdir(curated_dir), ["CDN-Hsmu_M2149.L4_001r.mei"])
        with open(curated, encoding="utf-8") as replaced:
            self.assertEqual(replaced.read(), self.mei)
        submission.refresh_from_db()
        self.assertEqual(submission.published_path, curated)

    def test_publishing_refuses_an_already_ambiguous_folio(self) -> None:
        curated_dir = path.join(self.mei_dir, "123723")
        makedirs(curated_dir, exist_ok=True)
        for name in ("A_001r.mei", "B_001r.mei"):
            with open(path.join(curated_dir, name), "w", encoding="utf-8") as dupe:
                dupe.write("<mei/>")

        submission = self.make_submission()
        with override_settings(MEI_FILES_DIR=self.mei_dir):
            result = publish_mei_submission_task.apply(
                kwargs={
                    "manuscript_ids": [submission.manuscript_id],
                    "submission_id": submission.pk,
                }
            )
        self.assertFalse(result.successful())
        submission.refresh_from_db()
        self.assertEqual(submission.status, SubmissionStatus.PENDING)

    def test_no_partial_files_are_left_behind(self) -> None:
        submission = self.make_submission()
        self.publish(submission)
        written = listdir(path.join(self.mei_dir, "123723"))
        self.assertEqual(written, ["cdn-hsmu-m2149l4_001r.mei"])
