import shutil
import tempfile
from os import path

from rest_framework.test import APITestCase
from django.core.management import call_command
from django.urls import reverse
from django.conf import settings

from cantusdata.views.search_text import SearchMEITextView, TextSearchException
from cantusdata.models import Manuscript, Folio

from solr.core import SolrConnection  # type: ignore[import-untyped]

MANUSCRIPT_ID = 991961
LU_PAGE = path.join(
    settings.TEST_MEI_FILES_PATH, str(MANUSCRIPT_ID), "LU-1961_0123.mei"
)


class TestSearchMEITextView(APITestCase):
    search_text_view = SearchMEITextView()

    @classmethod
    def setUpTestData(cls) -> None:
        source = Manuscript.objects.create(
            id=MANUSCRIPT_ID, name="Test Liber Usualis", siglum="LU-TEST"
        )
        Folio.objects.create(manuscript=source, number="0123", image_uri="lu_0123.jpg")

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        call_command(
            "index_manuscript_mei",
            str(MANUSCRIPT_ID),
            "--mei-dir",
            settings.TEST_MEI_FILES_PATH,
        )

    def search(self, q: str, **options: str) -> dict:
        url = reverse("search-mei-text-view")
        response = self.client.get(
            url, {"q": q, "manuscript_id": MANUSCRIPT_ID, **options}
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def count_text_line_docs(self) -> int:
        solr_conn = SolrConnection(settings.SOLR_TEST_SERVER)
        return solr_conn.query(
            "*:*",
            fq=f"type:mei_text_line AND manuscript_id:{MANUSCRIPT_ID}",
            rows=0,
        ).numFound

    def test_get_query_words(self) -> None:
        view = self.search_text_view
        with self.subTest("Words are normalized"):
            self.assertEqual(
                view.get_query_words("Mi-se-rére  MEI", True), ["miserere", "mei"]
            )
            self.assertEqual(
                view.get_query_words("Mi-se-rére", False), ["mi", "se", "rere"]
            )
        with self.subTest("Long words are cut to the indexed n-gram length"):
            self.assertEqual(
                view.get_query_words("abcdefghijklmnopq", True), ["abcdefghijklmno"]
            )
        with self.subTest("A query with no words is invalid"):
            with self.assertRaises(TextSearchException):
                view.get_query_words(" -¬: ", True)

    def test_create_query_string(self) -> None:
        view = self.search_text_view
        with self.subTest("Single line, syllables joined"):
            self.assertEqual(
                view.create_query_string(["a", "b"], True, False),
                "text_line_t:a AND text_line_t:b",
            )
        with self.subTest("Single line, syllables separate"):
            self.assertEqual(
                view.create_query_string(["a"], False, False), "text_line_syl_t:a"
            )
        with self.subTest("Multi-line"):
            self.assertEqual(
                view.create_query_string(["a", "b"], True, True),
                "text_window_t:a AND text_window_t:b AND "
                "((text_line_t:a AND text_line_t:b) OR "
                "(*:* -(text_next_t:a AND text_next_t:b)))",
            )

    def test_get(self) -> None:
        with self.subTest("Matches hyphenated, accented text"):
            response = self.search("miserere mei")
            self.assertEqual(response["numFound"], 1)
            result = response["results"][0]
            self.assertEqual(len(result["lines"]), 1)
            self.assertIn("Ps. 50", result["lines"][0])
            self.assertEqual(result["boxes"][0]["f"], "0123")
            self.assertEqual(result["boxes"][0]["p"], "lu_0123.jpg")
        with self.subTest("Results are in page order"):
            response = self.search("asperges")
            texts = [result["lines"][0] for result in response["results"]]
            self.assertEqual(texts[0], "The Asperges.")
            ys = [result["boxes"][0]["y"] for result in response["results"]]
            self.assertEqual(ys, sorted(ys))
        with self.subTest("No match"):
            self.assertEqual(self.search("alleluia")["numFound"], 0)
        with self.subTest("Missing or invalid parameters"):
            url = reverse("search-mei-text-view")
            for params in [
                {"q": "mei"},
                {"q": "--", "manuscript_id": MANUSCRIPT_ID},
                {"q": "mei", "manuscript_id": MANUSCRIPT_ID, "hyphens": "x"},
                {"q": "mei", "manuscript_id": MANUSCRIPT_ID, "multiline": "1"},
            ]:
                self.assertEqual(self.client.get(url, params).status_code, 400)

    def test_hyphens_option(self) -> None:
        # The line reads "se-ricórdi-am tú- am."
        with self.subTest("Ignored: syllables join into words"):
            self.assertEqual(self.search("ricordiam")["numFound"], 1)
        with self.subTest("Kept: text is matched syllable by syllable"):
            self.assertEqual(self.search("ricordiam", hyphens="keep")["numFound"], 0)
            self.assertEqual(
                self.search("se-ricordi-am", hyphens="keep")["numFound"], 1
            )

    def test_multiline_option(self) -> None:
        # "... et mundá¬" ends one line and "bor: lavá- bis me," starts the next.
        with self.subTest("A word split across lines needs multi-line"):
            self.assertEqual(self.search("mundabor")["numFound"], 0)
            response = self.search("mundabor", multiline="true")
            self.assertEqual(response["numFound"], 1)
            result = response["results"][0]
            self.assertEqual(len(result["lines"]), 2)
            self.assertTrue(result["lines"][1].startswith("bor:"))
            self.assertEqual(len(result["boxes"]), 2)
        with self.subTest("Joined across lines: 'mi¬' then 'se-ricórdi-am'"):
            self.assertEqual(self.search("misericordiam")["numFound"], 0)
            response = self.search("misericordiam", multiline="true")
            self.assertEqual(response["numFound"], 1)
            self.assertIn("Ps. 50", response["results"][0]["lines"][0])
        with self.subTest("A match within one line is listed once, at that line"):
            single = self.search("miserere mei")
            multi = self.search("miserere mei", multiline="true")
            self.assertEqual(multi["numFound"], single["numFound"])
            self.assertEqual(multi["results"], single["results"])

    def test_reindexing_updates_text(self) -> None:
        """
        Text lines are rebuilt whenever a folio's MEI is reindexed, so a
        correction to the MEI replaces the old text instead of adding to it.
        """
        line_count = self.count_text_line_docs()
        mei_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, mei_dir)
        # Restore the original index for the other tests.
        self.addCleanup(
            call_command,
            "index_manuscript_mei",
            str(MANUSCRIPT_ID),
            "--mei-dir",
            settings.TEST_MEI_FILES_PATH,
            "--replace",
        )
        manuscript_dir = path.join(mei_dir, str(MANUSCRIPT_ID))
        shutil.copytree(path.dirname(LU_PAGE), manuscript_dir)
        corrected_page = path.join(manuscript_dir, path.basename(LU_PAGE))
        with open(corrected_page, encoding="utf-8") as mei_file:
            content = mei_file.read()
        with open(corrected_page, "w", encoding="utf-8") as mei_file:
            mei_file.write(content.replace("The Ordinary Chants", "Corrected Heading"))

        call_command(
            "index_manuscript_mei",
            str(MANUSCRIPT_ID),
            "--mei-dir",
            mei_dir,
            "--folio",
            "0123",
            "--replace",
        )

        self.assertEqual(self.count_text_line_docs(), line_count)
        self.assertEqual(self.search("corrected heading")["numFound"], 1)
        self.assertEqual(self.search("ordinary chants")["numFound"], 0)

    def test_flush_index_removes_text(self) -> None:
        self.addCleanup(
            call_command,
            "index_manuscript_mei",
            str(MANUSCRIPT_ID),
            "--mei-dir",
            settings.TEST_MEI_FILES_PATH,
        )
        self.assertGreater(self.count_text_line_docs(), 0)
        call_command("index_manuscript_mei", str(MANUSCRIPT_ID), "--flush-index")
        self.assertEqual(self.count_text_line_docs(), 0)

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", str(MANUSCRIPT_ID), "--flush-index")
        super().tearDownClass()
