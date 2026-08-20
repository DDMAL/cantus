import os

from django.core.management import call_command
from django.test import TestCase
from django.conf import settings

from cantusdata.models import Manuscript, Folio
from cantusdata.test.core.helpers.mei_processing.test_mei_tokenizer import (
    calculate_expected_total_ngrams,
)

from solr.core import SolrConnection  # type: ignore

TEST_MEI_FILES_PATH = settings.TEST_MEI_FILES_PATH


class IndexManuscriptMeiTestCase(TestCase):
    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        # Create a manuscript
        manuscript = Manuscript.objects.create(id=123723)
        # Create two folios
        Folio.objects.create(number="001r", manuscript=manuscript)
        Folio.objects.create(number="001v", manuscript=manuscript)

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def test_index_manuscript_mei(self) -> None:
        # Assert that prior to the command run, the folio "999r" does not
        # exist in the database
        with self.assertRaises(Folio.DoesNotExist):
            Folio.objects.get(manuscript_id=123723, number="999r")
        call_command(
            "index_manuscript_mei",
            "123723",
            "--min-ngram",
            "1",
            "--max-ngram",
            "5",
            "--mei-dir",
            TEST_MEI_FILES_PATH,
        )
        # Assert that the folio "999r" now exists in the database
        # (will raise exception if it does not)
        with self.subTest("Test creation of non-existent folio"):
            Folio.objects.get(manuscript_id=123723, number="999r")
        results = self.solr_conn.query("*:*", fq="type:omr_ngram")
        with self.subTest("Test total number of indexed documents"):
            total_exp_ngrams_001r = calculate_expected_total_ngrams(
                f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_001r.mei", 1, 5
            )
            total_exp_ngrams_001v = calculate_expected_total_ngrams(
                f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_001v.mei", 1, 5
            )
            total_exp_ngrams_999r = calculate_expected_total_ngrams(
                f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_999r.mei", 1, 5
            )
            self.assertEqual(
                results.numFound,
                total_exp_ngrams_001r + total_exp_ngrams_001v + total_exp_ngrams_999r,
            )

    def test_flush_option(self) -> None:
        call_command(
            "index_manuscript_mei",
            "123723",
            "--mei-dir",
            TEST_MEI_FILES_PATH,
        )
        with self.subTest("Check index is not empty before test"):
            results = self.solr_conn.query("*:*", fq="type:omr_ngram")
            self.assertGreater(len(results), 0)

        with self.subTest("Test flush option"):
            call_command("index_manuscript_mei", "123723", "--flush-index")
            results = self.solr_conn.query("*:*", fq="type:omr_ngram")
            self.assertEqual(len(results), 0)


class IndexManuscriptMeiExceptionsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        # Create a manuscript
        manuscript = Manuscript.objects.create(id=123723)
        # Create two folios
        Folio.objects.create(number="001r", manuscript=manuscript)
        Folio.objects.create(number="001v", manuscript=manuscript)

    def setUp(self) -> None:
        os.mkdir("/empty-mei-dir")
        os.mkdir("/test-mei-dir")
        os.mkdir(
            "/test-mei-dir/123723",
        )
        with open("/test-mei-dir/123723/test.mei", "w") as f:
            pass

    def test_command_exceptions(self) -> None:
        with self.subTest("Test manuscript_id with no folios"):
            with self.assertRaises(ValueError):
                call_command(
                    "index_manuscript_mei", "123724", "--mei-dir", TEST_MEI_FILES_PATH
                )
        with self.subTest("Test non-existent mei-dir"):
            with self.assertRaises(FileNotFoundError):
                call_command(
                    "index_manuscript_mei", "123723", "--mei-dir", "/non-existent-dir"
                )
        with self.subTest("Test empty mei-dir"):
            with self.assertRaises(FileNotFoundError):
                call_command(
                    "index_manuscript_mei", "123723", "--mei-dir", "/empty-mei-dir"
                )
        with self.subTest("Test improperly named mei files"):
            with self.assertRaises(ValueError):
                call_command(
                    "index_manuscript_mei", "123723", "--mei-dir", "/test-mei-dir"
                )

    def tearDown(self) -> None:
        os.remove("/test-mei-dir/123723/test.mei")
        os.rmdir("/test-mei-dir/123723")
        os.rmdir("/test-mei-dir")
        os.rmdir("/empty-mei-dir")

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()


class IndexManuscriptMeiFolioScopingTestCase(TestCase):
    """
    Covers --folio and --replace, which together let one folio be reindexed
    without disturbing the rest of the manuscript. Publishing a single reviewed
    MEI submission depends on that: index_manuscript_mei takes one --mei-dir, so
    a whole-manuscript flush would drop every folio the directory does not hold.
    """

    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        manuscript = Manuscript.objects.create(id=123723)
        # image_uri set, unlike the cases above, so the command does not take its
        # "folio missing from the database" branch.
        Folio.objects.create(
            number="001r", image_uri="folio-001r", manuscript=manuscript
        )
        Folio.objects.create(
            number="001v", image_uri="folio-001v", manuscript=manuscript
        )
        Folio.objects.create(
            number="999r", image_uri="folio-999r", manuscript=manuscript
        )

    def setUp(self) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def index(self, *extra_args: str) -> None:
        call_command(
            "index_manuscript_mei",
            "123723",
            "--mei-dir",
            TEST_MEI_FILES_PATH,
            *extra_args,
        )

    def count_for_folio(self, folio: str) -> int:
        results = self.solr_conn.query(
            "*:*", fq=f'type:omr_ngram AND manuscript_id:123723 AND folio:"{folio}"'
        )
        return int(results.numFound)

    def expected_for_folio(self, folio: str) -> int:
        return calculate_expected_total_ngrams(
            f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_{folio}.mei", 1, 5
        )

    def test_folio_option_indexes_only_that_folio(self) -> None:
        self.index("--folio", "001r")
        self.assertEqual(self.count_for_folio("001r"), self.expected_for_folio("001r"))
        self.assertEqual(self.count_for_folio("001v"), 0)
        self.assertEqual(self.count_for_folio("999r"), 0)

    def test_indexing_a_folio_twice_without_replace_duplicates_it(self) -> None:
        """Documents why publishing must pass --replace."""
        self.index("--folio", "001r")
        self.index("--folio", "001r")
        self.assertEqual(
            self.count_for_folio("001r"), 2 * self.expected_for_folio("001r")
        )

    def test_replace_reindexes_a_folio_without_duplicating_it(self) -> None:
        self.index("--folio", "001r")
        self.index("--folio", "001r", "--replace")
        self.assertEqual(self.count_for_folio("001r"), self.expected_for_folio("001r"))

    def test_replacing_one_folio_leaves_its_siblings_alone(self) -> None:
        self.index()
        untouched_before = self.count_for_folio("001v")
        self.index("--folio", "001r", "--replace")
        self.assertEqual(self.count_for_folio("001r"), self.expected_for_folio("001r"))
        self.assertEqual(self.count_for_folio("001v"), untouched_before)
        self.assertGreater(untouched_before, 0)

    def test_flush_index_can_be_scoped_to_one_folio(self) -> None:
        self.index()
        call_command(
            "index_manuscript_mei", "123723", "--flush-index", "--folio", "001r"
        )
        self.assertEqual(self.count_for_folio("001r"), 0)
        self.assertGreater(self.count_for_folio("001v"), 0)

    def test_replace_without_folio_rebuilds_the_whole_manuscript(self) -> None:
        self.index()
        before = self.count_for_folio("001r") + self.count_for_folio("001v")
        self.index("--replace")
        after = self.count_for_folio("001r") + self.count_for_folio("001v")
        self.assertEqual(before, after)

    def test_folio_with_no_mei_file_is_an_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.index("--folio", "002v")

    def test_two_files_for_one_folio_is_an_error(self) -> None:
        """
        The folio is read from after the last underscore, so files with different
        prefixes can name the same folio and each contribute a full set of
        n-grams for it. That must fail loudly rather than double the folio.
        """
        import shutil
        import tempfile

        staging_dir = tempfile.mkdtemp(prefix="mei-dupe-test-")
        try:
            manuscript_dir = os.path.join(staging_dir, "123723")
            os.makedirs(manuscript_dir)
            source = f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_001r.mei"
            shutil.copy(source, os.path.join(manuscript_dir, "one_001r.mei"))
            shutil.copy(source, os.path.join(manuscript_dir, "two_001r.mei"))
            with self.assertRaises(ValueError):
                call_command("index_manuscript_mei", "123723", "--mei-dir", staging_dir)
        finally:
            shutil.rmtree(staging_dir, ignore_errors=True)
