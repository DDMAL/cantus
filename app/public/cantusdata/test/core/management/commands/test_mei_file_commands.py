from io import StringIO
from os import listdir, makedirs, path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from solr.core import SolrConnection  # type: ignore

from cantusdata.models import Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus

MEI_FIXTURE_DIR = path.join(settings.TEST_MEI_FILES_PATH, "123723")


class SeedMeiFilesTestCase(TestCase):
    """
    Seeding is what makes the live MEI tree a superset of the curated archive
    rather than a second, partial tree.
    """

    def setUp(self) -> None:
        self.mei_dir = mkdtemp(prefix="mei-files-test-")

    def tearDown(self) -> None:
        rmtree(self.mei_dir, ignore_errors=True)

    def seed(self, *extra_args: str) -> str:
        out = StringIO()
        with override_settings(MEI_FILES_DIR=self.mei_dir):
            call_command(
                "seed_mei_files",
                "123723",
                "--from",
                settings.TEST_MEI_FILES_PATH,
                *extra_args,
                stdout=out,
            )
        return out.getvalue()

    def test_curated_files_are_copied_into_the_live_tree(self) -> None:
        self.seed()
        self.assertEqual(
            sorted(listdir(path.join(self.mei_dir, "123723"))),
            sorted(listdir(MEI_FIXTURE_DIR)),
        )

    def test_existing_files_are_left_alone_by_default(self) -> None:
        """A published deposit must not be silently reverted to the curated copy."""
        self.seed()
        published = path.join(self.mei_dir, "123723", "cdn-hsmu-m2149l4_001r.mei")
        with open(published, "w", encoding="utf-8") as newer:
            newer.write("<mei>corrected</mei>")

        output = self.seed()
        with open(published, encoding="utf-8") as unchanged:
            self.assertEqual(unchanged.read(), "<mei>corrected</mei>")
        self.assertIn("--overwrite", output)

    def test_overwrite_replaces_existing_files(self) -> None:
        self.seed()
        published = path.join(self.mei_dir, "123723", "cdn-hsmu-m2149l4_001r.mei")
        with open(published, "w", encoding="utf-8") as newer:
            newer.write("<mei>corrected</mei>")

        self.seed("--overwrite")
        with open(published, encoding="utf-8") as restored:
            self.assertNotEqual(restored.read(), "<mei>corrected</mei>")

    def test_a_folio_already_present_under_another_name_is_not_duplicated(
        self,
    ) -> None:
        """
        A published deposit is named after the siglum slug, the curated archive
        after its own convention. Both name the same folio to the indexer, so
        seeding must not leave two files for one folio.
        """
        manuscript_dir = path.join(self.mei_dir, "123723")
        makedirs(manuscript_dir, exist_ok=True)
        deposited = path.join(manuscript_dir, "CDN-Hsmu_M2149.L4_001r.mei")
        with open(deposited, "w", encoding="utf-8") as published:
            published.write("<mei>deposited</mei>")

        self.seed()

        names = sorted(listdir(manuscript_dir))
        for_001r = [n for n in names if n.split("_")[-1].split(".")[0] == "001r"]
        self.assertEqual(for_001r, ["CDN-Hsmu_M2149.L4_001r.mei"])
        with open(deposited, encoding="utf-8") as untouched:
            self.assertEqual(untouched.read(), "<mei>deposited</mei>")

    def test_overwrite_replaces_a_differently_named_file_for_the_folio(self) -> None:
        manuscript_dir = path.join(self.mei_dir, "123723")
        makedirs(manuscript_dir, exist_ok=True)
        deposited = path.join(manuscript_dir, "CDN-Hsmu_M2149.L4_001r.mei")
        with open(deposited, "w", encoding="utf-8") as published:
            published.write("<mei>deposited</mei>")

        output = self.seed("--overwrite")

        names = sorted(listdir(manuscript_dir))
        for_001r = [n for n in names if n.split("_")[-1].split(".")[0] == "001r"]
        self.assertEqual(len(for_001r), 1)
        self.assertFalse(path.exists(deposited))
        self.assertIn("Replaced 1 file(s)", output)

    def test_missing_manuscript_directory_is_an_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            with override_settings(MEI_FILES_DIR=self.mei_dir):
                call_command(
                    "seed_mei_files",
                    "999999",
                    "--from",
                    settings.TEST_MEI_FILES_PATH,
                    stdout=StringIO(),
                )


class PublishedSubmissionCommandsTestCase(TestCase):
    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        with open(
            path.join(MEI_FIXTURE_DIR, "cdn-hsmu-m2149l4_001r.mei"), encoding="utf-8"
        ) as mei_file:
            cls.mei = mei_file.read()

    def setUp(self) -> None:
        self.mei_dir = mkdtemp(prefix="mei-files-test-")
        self.export_dir = mkdtemp(prefix="mei-export-test-")
        manuscript = Manuscript.objects.create(id=123723, siglum="CDN-Hsmu M2149.L4")
        folio = Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=manuscript
        )
        self.submission = MEISubmission.objects.create(
            manuscript=manuscript,
            folio=folio,
            folio_number="001r",
            mei=self.mei,
            submitter="asadra",
            status=SubmissionStatus.PUBLISHED,
        )
        makedirs(path.join(self.mei_dir, "123723"), exist_ok=True)

    def tearDown(self) -> None:
        rmtree(self.mei_dir, ignore_errors=True)
        rmtree(self.export_dir, ignore_errors=True)
        self.solr_conn.delete_query("type:omr_ngram AND manuscript_id:123723")
        self.solr_conn.commit()

    def indexed_count(self) -> int:
        results = self.solr_conn.query(
            "*:*", fq='type:omr_ngram AND manuscript_id:123723 AND folio:"001r"'
        )
        return int(results.numFound)

    def test_reindex_restores_a_missing_file_from_the_database(self) -> None:
        """
        The submitted MEI lives in Postgres, so the volume can always be rebuilt
        from it -- the recovery path if the volume is restored from an older
        backup than the database.
        """
        with override_settings(MEI_FILES_DIR=self.mei_dir):
            call_command("reindex_published_submissions", "123723", stdout=StringIO())
        expected = path.join(self.mei_dir, "123723", "cdn-hsmu-m2149l4_001r.mei")
        self.assertTrue(path.exists(expected))
        self.assertGreater(self.indexed_count(), 0)

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.published_path, expected)

    def test_reindex_is_idempotent(self) -> None:
        with override_settings(MEI_FILES_DIR=self.mei_dir):
            call_command("reindex_published_submissions", "123723", stdout=StringIO())
            first = self.indexed_count()
            call_command("reindex_published_submissions", "123723", stdout=StringIO())
        self.assertEqual(self.indexed_count(), first)

    def test_files_only_skips_indexing(self) -> None:
        with override_settings(MEI_FILES_DIR=self.mei_dir):
            call_command(
                "reindex_published_submissions",
                "123723",
                "--files-only",
                stdout=StringIO(),
            )
        self.assertTrue(
            path.exists(path.join(self.mei_dir, "123723", "cdn-hsmu-m2149l4_001r.mei"))
        )
        self.assertEqual(self.indexed_count(), 0)

    def test_export_writes_published_mei_for_the_curated_archive(self) -> None:
        call_command(
            "export_published_submissions",
            "123723",
            "--out",
            self.export_dir,
            stdout=StringIO(),
        )
        exported = path.join(self.export_dir, "123723", "cdn-hsmu-m2149l4_001r.mei")
        self.assertTrue(path.exists(exported))
        with open(exported, encoding="utf-8") as written:
            self.assertEqual(written.read(), self.mei)

    def test_export_ignores_unpublished_submissions(self) -> None:
        self.submission.status = SubmissionStatus.PENDING
        self.submission.save()
        out = StringIO()
        call_command(
            "export_published_submissions",
            "123723",
            "--out",
            self.export_dir,
            stdout=out,
        )
        self.assertIn("No published submissions", out.getvalue())
        self.assertFalse(path.exists(path.join(self.export_dir, "123723")))
