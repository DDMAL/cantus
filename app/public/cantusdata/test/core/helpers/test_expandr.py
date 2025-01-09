from itertools import combinations
from django.test import TestCase
from cantusdata.helpers.expandr import (
    expand_mode,
    expand_differentia,
    expand_office,
    GenreExpander,
    PositionExpander,
)


class ExpandrFunctionsTestCase(TestCase):
    def test_expand_mode(self) -> None:
        # Number and symbol ordering is important
        numbers = ["1", "2", "3", "4", "5", "6", "7", "8"]
        symbol_keys = ["*", "r", "?", "S", "T"]
        symbols = {
            "*": "No music",
            "r": "Formulaic",
            "?": "Uncertain",
            "S": "Responsory (special)",
            "T": "Chant in Transposition",
        }
        max_length = 3
        # Test every combination
        for combination in combinations(numbers + symbol_keys, max_length):
            expected_output = ""
            for character in combination:
                if character in numbers:
                    expected_output += str(character) + " "
                elif character in symbols:
                    expected_output += symbols[character] + " "
                else:
                    self.fail("Illegal character.")
            # There will be whitespace at the end that we want to deal with
            expected_output = expected_output.strip()
            # Merge the combination array into a string
            combination_string = ""
            for c in list(map(str, combination)):
                combination_string += c + " "
            # Test it
            self.assertEqual(expand_mode(combination_string), expected_output)

    def test_expand_genre(self) -> None:
        genre_expander = GenreExpander()
        self.assertEqual(genre_expander.expand_genre("A"), "Antiphon")
        self.assertEqual(genre_expander.expand_genre("AV"), "Antiphon verse")
        self.assertEqual(genre_expander.expand_genre("R"), "Responsory")
        self.assertEqual(genre_expander.expand_genre("V"), "Responsory verse")
        self.assertEqual(genre_expander.expand_genre("W"), "Versicle")
        self.assertEqual(genre_expander.expand_genre("H"), "Hymn")
        self.assertEqual(genre_expander.expand_genre("I"), "Invitatory antiphon")
        self.assertEqual(genre_expander.expand_genre("Pr"), "Prefatio")
        self.assertEqual(genre_expander.expand_genre("IP"), "Invitatory psalm")
        self.assertEqual(genre_expander.expand_genre("[M]"), '"Miscellaneous"')
        self.assertEqual(genre_expander.expand_genre("[G]"), "Mass chant")
        self.assertEqual(
            genre_expander.expand_genre("[?]"),
            "Unknown, ambiguous, unidentifiable, illegible",
        )
        self.assertEqual(genre_expander.expand_genre("Z"), "Z")

    def test_expand_differentia(self) -> None:
        self.assertEqual(expand_differentia("*"), "No differentia")
        # Test that whitespace is stripped
        self.assertEqual(expand_differentia("    *   "), "No differentia")
        # Test all other cases
        self.assertEqual(expand_differentia("Normal string"), "Normal string")

    def test_expand_office(self) -> None:
        self.assertEqual(expand_office("V"), "First Vespers")
        self.assertEqual(expand_office("C"), "Compline")
        self.assertEqual(expand_office("M"), "Matins")
        self.assertEqual(expand_office("L"), "Lauds")
        self.assertEqual(expand_office("P"), "Prime")
        self.assertEqual(expand_office("T"), "Terce")
        self.assertEqual(expand_office("S"), "Sext")
        self.assertEqual(expand_office("N"), "None")
        self.assertEqual(expand_office("V2"), "Second Vespers")
        self.assertEqual(expand_office("D"), "Day Hours")
        self.assertEqual(expand_office("R"), "Memorial")
        self.assertEqual(
            expand_office("E"), "Antiphons for the Magnificat or Benedictus"
        )
        self.assertEqual(
            expand_office("H"), "Antiphons based on texts from the Historia"
        )
        self.assertEqual(expand_office("CA"), "Chapter")
        self.assertEqual(expand_office("X"), "Supplementary")
        self.assertEqual(expand_office("125125"), "Error")


class PositionExpanderTestCase(TestCase):
    def setUp(self) -> None:
        self.position_expander = PositionExpander()

    def test_get_text(self) -> None:
        output = self.position_expander.expand_position("M", "A", "3. ")
        self.assertEqual("Antiphon for all Psalms of Nocturn 3", output)

    def test_get_nonexistant_text(self) -> None:
        output = self.position_expander.expand_position("Z", "Z", "Z")
        self.assertEqual("", output)
