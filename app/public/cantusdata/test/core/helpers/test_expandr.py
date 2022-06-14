from django.test import TestCase
from cantusdata.helpers import expandr
from itertools import combinations


class ExpandrFunctionsTestCase(TestCase):
    def test_expand_mode(self):
        # Number and symbol ordering is important
        numbers = [1, 2, 3, 4, 5, 6, 7, 8]
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
            self.assertEqual(expandr.expand_mode(combination_string), expected_output)

    def test_expand_genre(self):
        self.assertEqual(expandr.expand_genre("A"), "Antiphon")
        self.assertEqual(expandr.expand_genre("AV"), "Antiphon verse")
        self.assertEqual(expandr.expand_genre("R"), "Responsory")
        self.assertEqual(expandr.expand_genre("V"), "Responsory verse")
        self.assertEqual(expandr.expand_genre("W"), "Versicle")
        self.assertEqual(expandr.expand_genre("H"), "Hymn")
        self.assertEqual(expandr.expand_genre("I"), "Invitatory antiphon")
        self.assertEqual(expandr.expand_genre("Pr"), "Prefatio")
        self.assertEqual(expandr.expand_genre("IP"), "Invitatory psalm")
        self.assertEqual(expandr.expand_genre("M"), '"Miscellaneous"')
        self.assertEqual(expandr.expand_genre("G"), "Mass chant")
        self.assertEqual(
            expandr.expand_genre("?"), "Unknown, ambiguous, unidentifiable, illegible"
        )
        self.assertEqual(expandr.expand_genre("Z"), "Z")

    def test_expand_differentia(self):
        self.assertEqual(expandr.expand_differentia("*"), "No differentia")
        # Test that whitespace is stripped
        self.assertEqual(expandr.expand_differentia("    *   "), "No differentia")
        # Test all other cases
        self.assertEqual(expandr.expand_differentia("Normal string"), "Normal string")

    def test_expand_office(self):
        self.assertEqual(expandr.expand_office("V"), "First Vespers")
        self.assertEqual(expandr.expand_office("C"), "Compline")
        self.assertEqual(expandr.expand_office("M"), "Matins")
        self.assertEqual(expandr.expand_office("L"), "Lauds")
        self.assertEqual(expandr.expand_office("P"), "Prime")
        self.assertEqual(expandr.expand_office("T"), "Terce")
        self.assertEqual(expandr.expand_office("S"), "Sext")
        self.assertEqual(expandr.expand_office("N"), "None")
        self.assertEqual(expandr.expand_office("V2"), "Second Vespers")
        self.assertEqual(expandr.expand_office("D"), "Day Hours")
        self.assertEqual(expandr.expand_office("R"), "Memorial")
        self.assertEqual(
            expandr.expand_office("E"), "Antiphons for the Magnificat or Benedictus"
        )
        self.assertEqual(
            expandr.expand_office("H"), "Antiphons based on texts from the Historia"
        )
        self.assertEqual(expandr.expand_office("CA"), "Chapter")
        self.assertEqual(expandr.expand_office("X"), "Supplementary")
        self.assertEqual(expandr.expand_office("125125"), "Error")


class PositionExpanderTestCase(TestCase):

    position_expander = None

    def setUp(self):
        self.position_expander = expandr.PositionExpander()

    def test_get_text(self):
        output = self.position_expander.get_text("M", "A", "3. ")
        self.assertEqual("Antiphon for all Psalms of Nocturn 3", output)

    def test_get_nonexistant_text(self):
        output = self.position_expander.get_text("Z", "Z", "Z")
        self.assertEqual("", output)

    def test_add_text(self):
        new_text = "This is some text!"
        self.assertEqual("", self.position_expander.get_text("Z", "X", "Y"))
        self.position_expander.add_text("Z", "X", "Y", "This is the new text.")
        self.assertEqual(
            "This is the new text.", self.position_expander.get_text("Z", "X", "Y")
        )
        # We should get an exception if we try to add text to the same place
        with self.assertRaises(KeyError):
            self.position_expander.add_text("Z", "X", "Y", "This should not work.")

    def tearDown(self):
        self.position_expander = None
