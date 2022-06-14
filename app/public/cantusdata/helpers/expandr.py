from cantusdata.settings import BASE_DIR
from cantusdata.helpers.scrapers.genre import genres

import csv
import urllib.request, urllib.error, urllib.parse
import re
import os


def expand_mode(mode_code):
    input_list = mode_code.strip()
    mode_output = []
    if "1" in input_list:
        mode_output.append("1")
    if "2" in input_list:
        mode_output.append("2")
    if "3" in input_list:
        mode_output.append("3")
    if "4" in input_list:
        mode_output.append("4")
    if "5" in input_list:
        mode_output.append("5")
    if "6" in input_list:
        mode_output.append("6")
    if "7" in input_list:
        mode_output.append("7")
    if "8" in input_list:
        mode_output.append("8")
    if "*" in input_list:
        mode_output.append("No music")
    if "r" in input_list:
        mode_output.append("Formulaic")
    if "?" in input_list:
        mode_output.append("Uncertain")
    if "S" in input_list:
        mode_output.append("Responsory (special)")
    if "T" in input_list:
        mode_output.append("Chant in Transposition")
    outstring = " ".join(mode_output)
    return outstring


def expand_genre(genre_code):
    if genre_code in genres:
        description = genres[genre_code]
        # some extra stuff in parentheses is showing up
        paren = description.find("(")
        return description[: paren - 1] if paren != -1 else description

    # If nothing was found, return the original
    return genre_code


def expand_differentia(differentia_code):
    """
    In most cases, the differentia remains unmodified

    :param differentia_code:
    :return:
    """
    return "No differentia" if "*" in differentia_code else differentia_code


def expand_office(office_code):
    return {
        "V": "First Vespers",
        "C": "Compline",
        "M": "Matins",
        "L": "Lauds",
        "P": "Prime",
        "T": "Terce",
        "S": "Sext",
        "N": "None",
        "V2": "Second Vespers",
        "MI": "Mass",
        "MI1": "First Mass",
        "MI2": "Second Mass",
        "MI3": "Third Mass",
        "D": "Day Hours",
        "R": "Memorial",
        "E": "Antiphons for the Magnificat or Benedictus",
        "H": "Antiphons based on texts from the Historia",
        "CA": "Chapter",
        "X": "Supplementary",
    }.get(office_code, "Error")


class PositionExpander(object):

    position_data_base = None

    def __init__(self):
        self.csv_file = csv.DictReader(
            open(os.path.join(BASE_DIR, "data_dumps", "position_names.csv"))
        )
        self.position_data_base = dict()
        for row in self.csv_file:
            office_code = self.remove_double_dash(row["Office"]).strip()
            genre_code = self.remove_double_dash(row["Genre"]).strip()
            position_code = (
                self.remove_double_dash(row["Position"])
                .strip()
                .lstrip("0")
                .rstrip("._ ")
            )
            text = self.remove_double_dash(row["Text Phrase"]).strip()

            # We are creating a 3-dimensional dictionary for fast lookup of names
            self.add_text(office_code, genre_code, position_code, text)

    def get_text(self, office_code, genre_code, position_code):
        try:
            return self.position_data_base[office_code.strip()][genre_code.strip()][
                position_code.strip().lstrip("0").rstrip("._ ")
            ]
        except KeyError:
            # If it's not in the dictionary then we just use an empty string
            return ""

    def add_text(self, office, genre, position, text):
        """
        Add a record to self.position_data_base, which is a 3d dictionary.
        Raises KeyError if a dictionary position is already taken.
        """
        if office in self.position_data_base:
            if genre in self.position_data_base[office]:
                if position in self.position_data_base[office][genre]:
                    raise KeyError(
                        "Position record {0} {1} {2} already set to {3}!".format(
                            office,
                            genre,
                            position,
                            self.position_data_base[office][genre][position],
                        )
                    )
                else:
                    # Position doesn't exist, so we create it
                    self.position_data_base[office][genre].update({position: text})
            else:
                # Genre doesn't exist, so we create it and position
                self.position_data_base[office].update({genre: {position: text}})
        else:
            # Office doesn't exist, so we create office, genre, and position
            self.position_data_base.update({office: {genre: {position: text}}})

    def remove_double_dash(self, text):
        """
        Turns double dashes into empty strings
        """
        if text.strip() == "--":
            return ""
        else:
            return text
