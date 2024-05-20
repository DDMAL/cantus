from unittest import TestCase

from cantusdata.helpers.search_utils import validate_query, get_transpositions


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
            self.assertTrue(validate_query(valid_pitch_names, "pitch_names_invariant"))
            self.assertFalse(
                validate_query(invalid_pitch_names, "pitch_names_invariant")
            )
        with self.subTest("contour validation"):
            valid_contour = ["u", "d", "r"]
            invalid_contour = ["u", "d", "s", "r"]
            self.assertTrue(validate_query(valid_contour, "contour"))
            self.assertFalse(validate_query(invalid_contour, "contour"))
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
