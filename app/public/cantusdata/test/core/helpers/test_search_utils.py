from unittest import TestCase

from cantusdata.helpers.search_utils import (
    validate_query,
    get_transpositions,
    translate_interval_query_direction,
    volpiano_to_pitch_names,
    normalize_search_text,
)


class SearchUtilsTestCase(TestCase):
    def test_validate_query(self) -> None:
        with self.subTest("neume_names validation"):
            valid_neume_names = ["punctum", "scandicus-flexus", "porrectus"]
            invalid_neume_names = ["punctum", "flexus", "not_a_neume_name"]
            self.assertTrue(validate_query(valid_neume_names, "neume_names"))
            self.assertFalse(validate_query(invalid_neume_names, "neume_names"))
        with self.subTest("pitch_names validation"):
            valid_pitch_names = ["a", "b", "c", "f", "g"]
            invalid_pitch_names = ["d", "e", "x", "f"]
            self.assertTrue(validate_query(valid_pitch_names, "pitch_names"))
            self.assertFalse(validate_query(invalid_pitch_names, "pitch_names"))
            self.assertTrue(validate_query(valid_pitch_names, "pitch_names_transposed"))
            self.assertFalse(
                validate_query(invalid_pitch_names, "pitch_names_transposed")
            )
        with self.subTest("contour validation"):
            valid_contour = ["u", "d", "r"]
            invalid_contour = ["u", "d", "s", "r"]
            self.assertTrue(validate_query(valid_contour, "contour"))
            self.assertFalse(validate_query(invalid_contour, "contour"))
        with self.subTest("intervals validation"):
            valid_intervals = ["u2", "d3", "r", "d14", "u12"]
            invalid_intervals = ["u2", "d3", "r", "d14", "u12", "r8"]
            self.assertTrue(validate_query(valid_intervals, "intervals"))
            self.assertFalse(validate_query(invalid_intervals, "intervals"))
        with self.subTest("invalid query type"):
            self.assertFalse(validate_query(["a", "b", "c"], "not_a_query_type"))

    def test_get_transpositions(self) -> None:
        with self.subTest("Transpositions of 'ga'"):
            transpositions = get_transpositions(["g", "a"])
            expected_transpositions = [
                ["g", "a"],
                ["a", "b"],
                ["b", "c"],
                ["c", "d"],
                ["d", "e"],
                ["e", "f"],
                ["f", "g"],
            ]
            self.assertEqual(transpositions, expected_transpositions)
        with self.subTest("Transpositions of 'fgae'"):
            transpositions = get_transpositions(["f", "g", "a", "e"])
            expected_transpositions = [
                ["f", "g", "a", "e"],
                ["g", "a", "b", "f"],
                ["a", "b", "c", "g"],
                ["b", "c", "d", "a"],
                ["c", "d", "e", "b"],
                ["d", "e", "f", "c"],
                ["e", "f", "g", "d"],
            ]
            self.assertEqual(transpositions, expected_transpositions)

    def test_translate_interval_query_direction(self) -> None:
        query_elems = ["u2", "d3", "r", "d14", "u12"]
        expected_translated_query = ["2", "-3", "1", "-14", "12"]
        translated_query = translate_interval_query_direction(query_elems)
        self.assertEqual(translated_query, expected_translated_query)

    def test_volpiano_to_pitch_names(self) -> None:
        with self.subTest("Clef, spacing and barlines are skipped"):
            self.assertEqual(
                volpiano_to_pitch_names("1---f--gh--3---k"), ["f", "g", "a", "c"]
            )
        with self.subTest("Octaves map to the same pitch names"):
            self.assertEqual(
                volpiano_to_pitch_names("9abcdefghjklmnopqrs"),
                list("gabcdefgabcdefgabcd"),
            )
            self.assertEqual(volpiano_to_pitch_names("8"), ["f"])
        with self.subTest("Liquescents map to their plain pitch"):
            self.assertEqual(volpiano_to_pitch_names("fG()H"), list("fgfga"))
        with self.subTest("Accidentals are skipped"):
            self.assertEqual(volpiano_to_pitch_names("1-ij-Ij"), ["b", "b"])
        with self.subTest("Invalid characters"):
            self.assertIsNone(volpiano_to_pitch_names("1-f-t"))
            self.assertIsNone(volpiano_to_pitch_names("f g?"))
        with self.subTest("No notes"):
            self.assertIsNone(volpiano_to_pitch_names("1---3"))
            self.assertIsNone(volpiano_to_pitch_names(""))

    def test_normalize_search_text(self) -> None:
        with self.subTest("Hyphenated syllables join into words"):
            self.assertEqual(
                normalize_search_text("Ps. 50. Mi- se-rére mé-i, Dé-us"),
                "ps 50 miserere mei deus",
            )
        with self.subTest("Line-continuation marks join syllables"):
            self.assertEqual(
                normalize_search_text("non e-rubé¬ scam: exspé¬ ctant"),
                "non erubescam exspectant",
            )
        with self.subTest("Accents and ligatures are spelled out"):
            self.assertEqual(
                normalize_search_text("saécu-la Cǽli cœli Œ"), "saecula caeli coeli oe"
            )
        with self.subTest("Without joining, hyphens separate syllables"):
            self.assertEqual(
                normalize_search_text("Mi- se-rére mi¬\nse-ricórdi-am", False),
                "mi se rere mi se ricordi am",
            )
        with self.subTest("Joining works across a line break"):
            self.assertEqual(
                normalize_search_text("mi¬\nse-ricórdi-am"), "misericordiam"
            )
        with self.subTest("Punctuation-only text is empty"):
            self.assertEqual(normalize_search_text(" ¬ — : "), "")
