"""
Defines a class, MEIParser, that converts the contents of an MEI file into 
python types for ease of subsequent processing. 

Also defines some additional functions useful for analyzing contents of an MEI
file:
    - get_interval_between_neume_components: Computes the interval (in semitones)
        between two neume components.
    - get_contour_from_interval: Computes the contour of an interval.
    - analyze_neume: Analyzes a neume (a list of neume components) to determine its
        neume type, its intervals, and its contour.

Defines associated types for the data structures used by the parser.
"""

from xml.etree import ElementTree as ET
from typing import Tuple, Dict, List, TypedDict, Literal

# Mapping from pitch names to integer pitch class where C = 0
PITCH_CLASS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

# Mapping from neume contours to neume names
NEUME_GROUPS = {
    "": "Punctum",
    "u": "Pes",
    "d": "Clivis",
    "uu": "Scandicus",
    "ud": "Torculus",
    "du": "Porrectus",
    "s": "Distropha",
    "ss": "Tristopha",
    "sd": "Pressus",
    "dd": "Climacus",
    "ddu": "Climacus resupinus",
    "udu": "Torculus resupinus",
    "dud": "Porrectus flexus",
    "udd": "Pes subpunctis",
    "uud": "Scandicus flexus",
    "uudd": "Scandicus subpunctis",
    "dudd": "Porrectus subpunctis",
}

# A type for coordinates of bounding boxes
CoordinatesType = Tuple[int, int, int, int]


class Zone(TypedDict):
    """A type for zones (bounding boxes) in MEI files"""

    coordinates: CoordinatesType
    rotate: float


class NeumeComponent(TypedDict):
    """A type for neume components"""

    pname: str
    octave: int
    bounding_box: Zone


class Neume(TypedDict):
    """A type for neumes"""

    neume_type: str
    neume_components: List[NeumeComponent]
    intervals: List[int]
    contours: List[str]


class SyllableText(TypedDict):
    """A type for the text of a syllable"""

    text: str
    bounding_box: Zone


class Syllable(TypedDict):
    """A type for syllables"""

    text: SyllableText
    neumes: List[Neume]


class MEIParser:
    """
    A class providing methods for parsing MEI files into python types.

    Initializes with a path to an MEI file:
        parser = MEIParser("path/to/mei/file.mei")

    An MEIParser object will have the following attributes after initialization,
    containg data from the MEI file:
        - zones: A dictionary of zones (bounding boxes) defined in the MEI file.
                The keys of this dictionary are the zone IDs and the values are
                ZONE dictionaries containing the zone coordinates and rotation.
        - syllables: A list of syllables parsed from the MEI file. Each syllable contains
                the syllable text and a list of neumes in the syllable.
    """

    # Namespaces used in MEI files
    MEINS = "{http://www.music-encoding.org/ns/mei}"
    XMLNS = "{http://www.w3.org/XML/1998/namespace}"

    def __init__(self, mei_file: str):
        self.mei_file = mei_file
        self.mei = ET.parse(self.mei_file)
        self.zones = self.parse_zones()
        self.syllables = self.parse_mei()

    def parse_zones(self) -> Dict[str, Zone]:
        """
        Get the zones (bounding boxes) in an MEI file from its
        ElementTree object.

        :param mei: ElementTree object of an MEI file
        :return: Dictionary of zones. Keys are the zone ID and values are
                    dictionaries containing zone "coordinates" and a "rotate"
                    value.
        """
        zones = {}
        for zone in self.mei.iter(f"{self.MEINS}zone"):
            zone_id = zone.get(f"{self.XMLNS}id")
            coordinates = (
                int(zone.get("ulx", 0)),
                int(zone.get("uly", 0)),
                int(zone.get("lrx", 0)),
                int(zone.get("lry", 0)),
            )
            rotate = float(zone.get("rotate", 0.0))
            zone_dict: Zone = {
                "coordinates": coordinates,
                "rotate": rotate,
            }
            zones[f"#{zone_id}"] = zone_dict
        return zones

    def _get_element_zone(self, element: ET.Element) -> Zone:
        """
        Get the coordinates of an element, returning
        (-1,-1,-1,-1) if none are found.

        :param element: An ElementTree element
        :return: Tuple of coordinates of the element
        """
        facs = element.get("facs")
        if facs:
            zone = self.zones.get(
                facs, {"coordinates": (-1, -1, -1, -1), "rotate": 0.0}
            )
            return zone
        return {"coordinates": (-1, -1, -1, -1), "rotate": 0.0}

    def parse_syllable(self, syllable: ET.Element) -> Syllable:
        """
        Parse a syllable element from an MEI file into a dictionary.

        :param syllable: An ElementTree element of a syllable
        :return: Dictionary of syllable data
        """
        # <syl> elements contain the text of the syllable.
        syl = syllable.find(f"{self.MEINS}syl")
        text_dict: SyllableText
        if syl and syl.text:
            text_dict = {
                "text": syl.text.strip(),
                "bounding_box": self._get_element_zone(syl),
            }
        else:
            text_dict = {
                "text": "",
                "bounding_box": {"coordinates": (-1, -1, -1, -1), "rotate": 0.0},
            }
        # <neume> elements contain the pitches of the syllable.
        neumes_list: List[Neume] = []
        for neume in syllable.findall(f"{self.MEINS}neume"):
            neume_components: List[NeumeComponent] = []
            for neume_comp in neume.findall(f"{self.MEINS}nc"):
                pname = neume_comp.get("pname")
                octave = neume_comp.get("oct")
                if pname and octave:
                    neume_components.append(
                        {
                            "pname": pname,
                            "octave": int(octave),
                            "bounding_box": self._get_element_zone(neume_comp),
                        }
                    )
            neume_type, intervals, contours = analyze_neume(neume_components)
            neume_dict: Neume = {
                "neume_type": neume_type,
                "neume_components": neume_components,
                "intervals": intervals,
                "contours": contours,
            }
            neumes_list.append(neume_dict)
        syllable_dict: Syllable = {
            "text": text_dict,
            "neumes": neumes_list,
        }
        return syllable_dict

    def parse_mei(self) -> List[Syllable]:
        """
        Parses the MEI file into a list of syllables.

        :return: A list of syllables
        """
        syllables = []
        for syllable in self.mei.iter(f"{self.MEINS}syllable"):
            syllable_dict = self.parse_syllable(syllable)
            syllables.append(syllable_dict)
        return syllables


def get_interval_between_neume_components(
    neume_component_1: NeumeComponent,
    neume_component_2: NeumeComponent,
) -> int:
    """
    Compute the interval (in semitones) between two
    pitches. Does this by converting the pitches to MIDI note
    numbers and then subtracting to get difference in semitones.
    Note: All B's, whether they would be performed as Bb or B,
    are treated as B.

    :param neume_component_1: A dictionary containing neume component information
    :param neume_component_2: A dictionary containing neume component information
    :return: The interval between the two pitches (in semitones)
    """
    pc1 = PITCH_CLASS[neume_component_1["pname"]]
    pc2 = PITCH_CLASS[neume_component_2["pname"]]
    # In MIDI note numbers, C0 = 12.
    pitch_1 = pc1 + (12 * (neume_component_1["octave"] + 1))
    pitch_2 = pc2 + (12 * (neume_component_2["octave"] + 1))
    return pitch_2 - pitch_1


def get_contour_from_interval(interval: int) -> Literal["u", "d", "s"]:
    """
    Compute the contour of an interval.

    :param interval: The size of the interval in semitones
    :return: The contour of the interval ("u"[p], "d"[own], or "s"[tay])
    """
    if interval < 0:
        return "d"
    if interval > 0:
        return "u"
    return "s"


def analyze_neume(neume: List[NeumeComponent]) -> Tuple[str, List[int], List[str]]:
    """
    Analyze a neume (a list of neume components) to determine:
    - Neume type
    - Neume intervals
    - Neume contour

    :param neume: A list of neume components (a list of NeumeComponentsType dictionaries)
    :return: A tuple of information about the neume:
                - Neume type (str)
                - Neume intervals (list of ints)
                - Neume contour (list of "u"[p], "d"[own], or "s"[tay])
    """
    intervals: List[int] = [
        get_interval_between_neume_components(nc1, nc2)
        for nc1, nc2 in zip(neume[:-1], neume[1:])
    ]
    contours: List[str] = [get_contour_from_interval(i) for i in intervals]
    neume_type: str = NEUME_GROUPS.get("".join(contours), "Compound")
    return neume_type, intervals, contours
