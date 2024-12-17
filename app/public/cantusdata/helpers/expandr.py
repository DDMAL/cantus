import json
import os
import requests

from django.conf import settings


def expand_mode(mode_code: str) -> str:
    """
    Translate non-numeric components of a CantusDB mode code into human-readable form.

    :param mode_code str: A CantusDB mode code
    :return: A human-readable translation of the mode code
    """
    mode_code_stripped = mode_code.strip()
    mode_output = []
    for char in mode_code_stripped:
        if char in "12345678":
            mode_output.append(char)
            continue
        match char:
            case "*":
                mode_output.append("No music")
            case "r":
                mode_output.append("Formulaic")
            case "?":
                mode_output.append("Uncertain")
            case "S":
                mode_output.append("Responsory (special)")
            case "T":
                mode_output.append("Chant in Transposition")
    outstring = " ".join(mode_output)
    return outstring


class GenreExpander:
    """
    Loads the genre mapping from the CantusDB API and provides a method to retrieve
    the full text genre description based on the given genre code.
    """

    cantus_db_api_endpoint = "https://cantusdatabase.org/genres"
    request_headers = {"Accept": "application/json"}

    def __init__(self) -> None:
        self.genre_data = self.load_genre_data()

    def load_genre_data(self) -> dict[str, str]:
        """
        Loads the genre list from the CantusDB API and returns a dictionary mapping
        genre codes to genre descriptions.
        """
        response = requests.get(
            self.cantus_db_api_endpoint, headers=self.request_headers, timeout=5
        )
        response.raise_for_status()
        genre_map: dict[str, str] = {
            x["name"]: x["description"] for x in response.json()["genres"]
        }
        return genre_map

    def expand_genre(self, genre_code: str) -> str:
        """
        Gets the genre description based on the genre code.
        """
        if genre_code in self.genre_data:
            description = self.genre_data[genre_code]
            # some extra stuff in parentheses is showing up
            paren = description.find("(")
            return description[: paren - 1] if paren != -1 else description

        # If nothing was found, return the original
        return genre_code


def expand_differentia(differentia_code: str) -> str:
    """
    In most cases, the differentia remains unmodified

    :param differentia_code: The differentia.
    :return str: "No differentia" if no differentia is present, otherwise the differentia.
    """
    return "No differentia" if "*" in differentia_code else differentia_code


OFFICE_CODES = {
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
}


def expand_office(office_code: str) -> str:
    """
    Returns the full name of the office based on the given office code.

    :param office_code: The office code.
    :return: The full name of the office.
    """
    return OFFICE_CODES.get(office_code, "Error")


class PositionExpander:
    """
    Loads the position mapping data from a JSON file and provides a method to retrieve
    the full text position description based on the given office, genre, and position code.
    """

    def __init__(self) -> None:
        with open(
            os.path.join(
                settings.BASE_DIR, "cantusdata", "helpers", "position_mapping.json"
            ),
            "r",
            encoding="utf-8",
        ) as f:
            self.position_data_base: dict[str, dict[str, dict[str, str]]] = json.load(f)

    def expand_position(
        self, office_code: str, genre_code: str, position_code: str
    ) -> str:
        """
        Retrieves the full text position description based on the given office, genre,
        and position code.
        """
        try:
            return self.position_data_base[office_code.strip()][genre_code.strip()][
                position_code.strip().lstrip("0").rstrip("._ ")
            ]
        except KeyError:
            # If it's not in the dictionary then we just use an empty string
            return ""
