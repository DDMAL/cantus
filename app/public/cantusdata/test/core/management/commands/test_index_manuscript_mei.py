import os

from django.core.management import call_command
from django.test import TestCase
from django.conf import settings

from cantusdata.management.commands.index_manuscript_mei import escape_solr_phrase
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


class FlushIndexEscapingTestCase(TestCase):
    """
    The folio is interpolated into a quoted Solr phrase that becomes a *delete*.
    Folio numbers are canonical Folio.number values today, so none carry a quote
    -- but an unescaped one would close the phrase early and leave the remainder
    as query syntax, deleting more of the index than the caller named.
    """

    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        manuscript = Manuscript.objects.create(id=123723)
        for number in ("001r", "001v"):
            Folio.objects.create(
                number=number, image_uri=f"folio-{number}", manuscript=manuscript
            )

    def setUp(self) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        call_command("index_manuscript_mei", "123723", "--mei-dir", TEST_MEI_FILES_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def total_indexed(self) -> int:
        results = self.solr_conn.query(
            "*:*", fq="type:omr_ngram AND manuscript_id:123723", rows=0
        )
        return int(results.numFound)

    def test_escaping_is_applied_to_quotes_and_backslashes(self) -> None:
        self.assertEqual(escape_solr_phrase("001r"), "001r")
        self.assertEqual(escape_solr_phrase('a"b'), 'a\\"b')
        # The backslash is doubled first, so the escape added for the quote is
        # not itself escaped away.
        self.assertEqual(escape_solr_phrase('a\\"b'), 'a\\\\\\"b')

    def folio_count(self, folio: str) -> int:
        results = self.solr_conn.query(
            "*:*",
            fq=f'type:omr_ngram AND manuscript_id:123723 AND folio:"{folio}"',
            rows=0,
        )
        return int(results.numFound)

    def test_an_injected_folio_does_not_widen_the_delete(self) -> None:
        """
        The payload is deliberately balanced: `001r" OR folio:"001v` closes the
        phrase and opens another, so unescaped it becomes the perfectly valid
        `folio:"001r" OR folio:"001v"` and deletes both folios. An unbalanced
        payload would only earn a Solr syntax error; this one silently deletes
        more than it names, which is the case worth pinning.

        Escaped, it names one folio that does not exist, so nothing goes.
        """
        before_001r = self.folio_count("001r")
        before_001v = self.folio_count("001v")
        self.assertGreater(before_001r, 0)
        self.assertGreater(before_001v, 0)

        call_command(
            "index_manuscript_mei",
            "123723",
            "--flush-index",
            "--folio",
            '001r" OR folio:"001v',
        )

        self.assertEqual(self.folio_count("001r"), before_001r)
        self.assertEqual(self.folio_count("001v"), before_001v)

    def test_a_real_folio_is_still_flushed(self) -> None:
        """The escaping must not break the ordinary case it wraps."""
        before = self.total_indexed()
        call_command(
            "index_manuscript_mei", "123723", "--flush-index", "--folio", "001r"
        )
        after = self.total_indexed()
        self.assertLess(after, before)
        self.assertGreater(after, 0)


class IndexManuscriptMeiNullImageUriTestCase(TestCase):
    """
    Folio.image_uri is nullable, and a folio can carry a null one while still
    having an MEI file: the command's "folio missing from the database" branch
    compares against "", so a None slips past it and is never repaired.

    A None reaching Solr is dropped rather than stored, leaving documents with
    no image_uri field at all -- which SearchNotationView then read by key,
    raising KeyError and returning a 500 for any query whose result page held
    one. The documents must carry an empty image_uri instead.
    """

    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        manuscript = Manuscript.objects.create(id=123723)
        # No image_uri, so both are stored as NULL.
        Folio.objects.create(number="001r", manuscript=manuscript)
        Folio.objects.create(number="001v", manuscript=manuscript)

    def setUp(self) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def test_documents_for_a_null_image_uri_folio_still_carry_the_field(self) -> None:
        call_command(
            "index_manuscript_mei",
            "123723",
            "--mei-dir",
            TEST_MEI_FILES_PATH,
        )
        # Scoped to 001r: folio 999r is absent from the database entirely, so it
        # takes the #891 branch and picks up the "" default rather than the None.
        results = self.solr_conn.query(
            "*:*",
            fq='type:omr_ngram AND manuscript_id:123723 AND folio:"001r"',
            rows=200,
        )
        self.assertGreater(len(results.results), 0)
        missing = [d for d in results.results if "image_uri" not in d]
        self.assertEqual(
            missing,
            [],
            "every indexed document should carry an image_uri, empty or not",
        )
        self.assertTrue(all(d["image_uri"] == "" for d in results.results))
