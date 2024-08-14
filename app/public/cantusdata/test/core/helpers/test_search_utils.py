from unittest import TestCase

from cantusdata.helpers.search_utils import (
    validate_query,
    get_transpositions,
    translate_interval_query_direction,
)


class SearchUtilsTestCase(TestCase):
    def test_validate_query(self) -> None:
        with self.subTest("neume_names validation"):
            valid_neume_names = ["punctum", "flexus", "porrectus"]
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
