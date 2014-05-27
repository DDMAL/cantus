from django.test import TestCase
from cantusdata.helpers import expandr
from itertools import combinations


class ExpandrFunctionsTestCase(TestCase):

    def test_ordinal(self):
        self.assertEquals(expandr.ordinal("error"), "error")
        self.assertEquals(expandr.ordinal(1), "1st")
        self.assertEquals(expandr.ordinal(2), "2nd")
        self.assertEquals(expandr.ordinal(3), "3rd")
        self.assertEquals(expandr.ordinal(4), "4th")
        self.assertEquals(expandr.ordinal(5), "5th")
        self.assertEquals(expandr.ordinal(6), "6th")
        self.assertEquals(expandr.ordinal(7), "7th")
        self.assertEquals(expandr.ordinal(8), "8th")
        self.assertEquals(expandr.ordinal(9), "9th")
        self.assertEquals(expandr.ordinal(10), "10th")
        self.assertEquals(expandr.ordinal(11), "11th")
        self.assertEquals(expandr.ordinal(12), "12th")

    def test_feast_code_lookup(self):
        pass

    def test_expand_mode(self):
        # Number and symbol ordering is important
        numbers = [1,2,3,4,5,6,7,8]
        symbol_keys = ["*", "r", "?", "S", "T"]
        symbols = {"*": "No music", "r": "Responsory (simple)",
                   "?": "Uncertain", "S": "Responsory (special)",
                   "T": "Chant in Transposition"}
        max_length = 3
        # Test every combination
        for combination in combinations(numbers + symbol_keys, max_length):
            expected_output = ""
            for character in combination:
                if character in numbers:
                    expected_output += "Mode " + str(character) + " "
                elif character in symbols:
                    expected_output += (symbols[character] + " ")
                else:
                    self.fail("Illegal character.")
            # There will be whitespace at the end that we want to deal with
            expected_output = expected_output.strip()
            # Merge the combination array into a string
            combination_string = ""
            for c in (map(str, combination)):
                combination_string += (c + " ")
            # Test it
            self.assertEqual(expandr.expand_mode(combination_string),
                             expected_output)


    def recursive_permutations_helper(depth, symbols, outputs_so_far):
        """
        A helper for test_expand_mode()
        """
        outputs = list()
        for symbol in symbols:
            for current in outputs_so_far:
                outputs.append(current + symbol)

    def test_expand_genre(self):
        self.assertEquals(expandr.expand_genre("A"), "Antiphon")
        self.assertEquals(expandr.expand_genre("AV"), "Antiphon Verse")
        self.assertEquals(expandr.expand_genre("R"), "Responsory")
        self.assertEquals(expandr.expand_genre("V"), "Responsory Verse")
        self.assertEquals(expandr.expand_genre("W"), "Versicle")
        self.assertEquals(expandr.expand_genre("H"), "Hymn")
        self.assertEquals(expandr.expand_genre("I"), "Invitatory antiphon")
        self.assertEquals(expandr.expand_genre("P"), "Invitatory Psalm")
        self.assertEquals(expandr.expand_genre("M"), "Miscellaneous")
        self.assertEquals(expandr.expand_genre("G"), "Mass chants")
        self.assertEquals(expandr.expand_genre("Z"), "Error")

    def test_expand_office(self):
        self.assertEquals(expandr.expand_office("V"), "First Vespers")
        self.assertEquals(expandr.expand_office("C"), "Compline")
        self.assertEquals(expandr.expand_office("M"), "Matins")
        self.assertEquals(expandr.expand_office("L"), "Lauds")
        self.assertEquals(expandr.expand_office("P"), "Prime")
        self.assertEquals(expandr.expand_office("T"), "Terce")
        self.assertEquals(expandr.expand_office("S"), "Sext")
        self.assertEquals(expandr.expand_office("N"), "None")
        self.assertEquals(expandr.expand_office("V2"), "Second Vespers")
        self.assertEquals(expandr.expand_office("D"), "Day Hours")
        self.assertEquals(expandr.expand_office("R"), "Memorial")
        self.assertEquals(expandr.expand_office("E"), "Antiphons for the Magnificat or Benedictus")
        self.assertEquals(expandr.expand_office("H"), "Antiphons based on texts from the Historia")
        self.assertEquals(expandr.expand_office("CA"), "Chapter")
        self.assertEquals(expandr.expand_office("X"), "Supplementary")
        self.assertEquals(expandr.expand_office("125125"), "Error")


class PositionExpanderTestCase(TestCase):

    position_expander = None

    def setUp(self):
        self.position_expander = expandr.PositionExpander()

    def test_get_text(self):
        output = self.position_expander.get_text("E", "A", "4")
        self.assertEqual("4th Antiphon for the Magnificat or Benidictus", output)

    def test_get_nonexistant_text(self):
        output = self.position_expander.get_text("Z", "Z", "Z")
        self.assertEqual("", output)

    def test_add_text(self):
        new_text = "This is some text!"
        self.assertEqual("", self.position_expander.get_text("Z", "X", "Y"))
        self.position_expander.add_text("Z", "X", "Y", "This is the new text.")
        self.assertEqual("This is the new text.",
                         self.position_expander.get_text("Z", "X", "Y"))
        # We should get an exception if we try to add text to the same place
        with self.assertRaises(KeyError):
            self.position_expander.add_text("Z", "X", "Y",
                                            "This should not work.")

    def tearDown(self):
        self.position_expander = None