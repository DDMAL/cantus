import json
from os import path
from unittest import TestCase

from django.conf import settings

from cantusdata.helpers.mei_processing.mei_tokenizer import MEITokenizer

# A Liber Usualis page: its text is OCR'd lines ('l' elements), not syllables.
LU_PAGE_PATH = path.join(settings.TEST_MEI_FILES_PATH, "991961", "LU-1961_0123.mei")


class MEITextLinesTestCase(TestCase):
    def setUp(self) -> None:
        self.tokenizer = MEITokenizer(LU_PAGE_PATH, min_ngram=1, max_ngram=5)

    def test_parse_text_lines(self) -> None:
        lines = self.tokenizer.parse_text_lines()
        self.assertEqual(len(lines), 17)
        self.assertEqual(lines[0]["text"], "The Ordinary Chants")
        self.assertEqual(lines[0]["bounding_box"]["coordinates"], (214, 182, 1294, 306))
        # Accents in these files are decomposed (e + combining accent), so
        # compare the start of the line, which has none.
        self.assertTrue(
            lines[-1]["text"].startswith("On the second Sunday of the Passion")
        )

    def test_create_text_line_documents(self) -> None:
        docs = self.tokenizer.create_text_line_documents()
        self.assertEqual(len(docs), 17)
        self.assertEqual([doc["line_order_i"] for doc in docs], list(range(17)))
        self.assertTrue(all(doc["type"] == "mei_text_line" for doc in docs))
        self.assertEqual(
            json.loads(docs[0]["location_json"]),
            [{"ulx": 214, "uly": 182, "width": 1080, "height": 124}],
        )
        psalm_line = next(doc for doc in docs if "Ps. 50" in doc["text_line_stored"])
        self.assertIn("miserere mei deus", psalm_line["text_line_t"])
        self.assertIn("mi se rere me i de us", psalm_line["text_line_syl_t"])

    def test_text_line_documents_carry_the_next_line(self) -> None:
        docs = self.tokenizer.create_text_line_documents()
        psalm_index = next(
            i for i, doc in enumerate(docs) if "Ps. 50" in doc["text_line_stored"]
        )
        psalm_line, next_line = docs[psalm_index], docs[psalm_index + 1]
        self.assertEqual(
            psalm_line["next_text_line_stored"], next_line["text_line_stored"]
        )
        self.assertEqual(psalm_line["next_location_stored"], next_line["location_json"])
        self.assertEqual(psalm_line["text_next_t"], next_line["text_line_t"])
        # "mi¬" ends the line and "se-ricórdi-am" starts the next.
        self.assertIn("misericordiam", psalm_line["text_window_t"])
        self.assertIn("mi se ricordi am", psalm_line["text_window_syl_t"])
        with self.subTest("The last line has no next line"):
            self.assertNotIn("next_text_line_stored", docs[-1])
            self.assertEqual(docs[-1]["text_window_t"], docs[-1]["text_line_t"])

    def test_files_without_text_lines(self) -> None:
        tokenizer = MEITokenizer(
            path.join(
                settings.TEST_MEI_FILES_PATH, "123723", "cdn-hsmu-m2149l4_001r.mei"
            ),
            min_ngram=1,
            max_ngram=5,
        )
        self.assertEqual(tokenizer.create_text_line_documents(), [])
