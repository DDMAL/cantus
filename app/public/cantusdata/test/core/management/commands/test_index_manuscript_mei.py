import os

from django.core.management import call_command
from django.test import TestCase
from django.conf import settings

from cantusdata.models import Manuscript, Folio
from cantusdata.test.core.helpers.mei_processing.test_mei_tokenizer import (
    calculate_expected_total_ngrams,
)

from solr.core import SolrConnection  # type: ignore


TEST_MEI_FILES_PATH = "cantusdata/test/core/helpers/mei_processing/test_mei_files"


class IndexManuscriptMeiTestCase(TestCase):
    solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)

    @classmethod
    def setUpTestData(cls) -> None:
        # Create a manuscript
        manuscript = Manuscript.objects.create(id=123723)
        # Create two folios
        Folio.objects.create(number="001r", manuscript=manuscript)
        Folio.objects.create(number="001v", manuscript=manuscript)

    def test_index_manuscript_mei(self) -> None:
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
        results = self.solr_conn.query("*:*", fq="type:omr_ngram")
        with self.subTest("Test total number of indexed documents"):
            total_exp_ngrams_001r = calculate_expected_total_ngrams(
                f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_001r.mei", 1, 5
            )
            total_exp_ngrams_001v = calculate_expected_total_ngrams(
                f"{TEST_MEI_FILES_PATH}/123723/cdn-hsmu-m2149l4_001v.mei", 1, 5
            )
            self.assertEqual(
                results.numFound, total_exp_ngrams_001r + total_exp_ngrams_001v
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
