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
from typing import Tuple, Dict, List, TypedDict, Literal, Iterator, Optional
from typing_extensions import TypeAlias

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
CoordinatesType: TypeAlias = Tuple[int, int, int, int]
"""
A type for coordinates of bounding boxes. The coordinates
of the box are given as four integers designating, in order:
    - the x-coordinate of the upper-left corner of the box
    - the y-coordinate of the upper-left corner of the box
    - the x-coordinate of the lower-right corner of the box
    - the y-coordinate of the lower-right corner of the box
"""


class Zone(TypedDict):
    """A type for zones (bounding boxes) in MEI files.

    coordinates: The location of the bounding box as
        defined in MEI 'zone' elements as a tuple of
        type CoordinatesType.
    rotate: The rotation of the zone in degrees.
    """

    coordinates: CoordinatesType
    rotate: float


class NeumeComponent(TypedDict):
    """A type for neume components

    pname: The pitch name of the neume component (ie. "c", "d", "e", etc.)
    octave: The octave of the neume component (as an integer, in scientific
        pitch notation; e.g. middle c has octave "4")
    bounding_box: The bounding box of the neume component
    """

    pname: str
    octave: int
    bounding_box: Zone


ContourType = Literal["u", "d", "s"]


class Neume(TypedDict):
    """A type for neumes

    neume_type: The name of the neume (ie. "Punctum", "Pes", "Clivis", etc.)
    neume_components: A list of neume components (containing pitch infomation)
    intervals: A list of intervals (in semitones) between neume components.
        In most cases, the length of this list is the same as the number of neume
        components in the neume, with the final element being the interval between
        the final component of the current neume and the first component of the
        following neume. When there is no following neume (at the end of the mei
        file), the list is one element shorter than the number of neume components
        (this final element is omitted).
    contours: A list of contours ("u"[p], "d"[own], or "s"[tay]) for each interval.
        As with the "intervals" list, the length of this list usually includes a final
        element that stores the contour between the final component of the current neume
        and the first component of the following neume.
    """

    neume_type: str
    neume_components: List[NeumeComponent]
    intervals: List[int]
    contours: List[ContourType]


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

    def _parse_syllable_text(self, syl_elem: Optional[ET.Element]) -> SyllableText:
        """
        Get the text of a syllable and its associated bounding box from
        a 'syl' element.

        :param syllable: A syllable element from an MEI file
        :return: Dictionary of syllable text data
        """
        if syl_elem is not None and syl_elem.text:
            text_dict: SyllableText = {
                "text": syl_elem.text.strip(),
                "bounding_box": self._get_element_zone(syl_elem),
            }
        else:
            text_dict = {
                "text": "",
                "bounding_box": {"coordinates": (-1, -1, -1, -1), "rotate": 0.0},
            }
        return text_dict

    def _parse_neume_component(
        self, neume_comp: ET.Element
    ) -> Optional[NeumeComponent]:
        """
        Parses an 'nc' element into a NeumeComponent dictionary.

        :param neume_comp: An 'nc' element from an MEI file
        :return: A dictionary of neume component data (see NeumeComponent for structure)
        """
        pname = neume_comp.get("pname")
        octave = neume_comp.get("oct")
        if pname and octave:
            return {
                "pname": pname,
                "octave": int(octave),
                "bounding_box": self._get_element_zone(neume_comp),
            }
        return None

    def _parse_neume(
        self,
        neume_components: List[ET.Element],
        next_neume_component: Optional[ET.Element],
    ) -> Neume:
        """
        Gets a Neume dictionary from a series of 'nc' elements (including
        the first neume component of the following neume, if it exists)

        :param neume_components: A list of 'nc' elements in a given 'neume' element
        :param next_neume_component: The first 'nc' element of the next neume
        :return: A list of neume dictionaries (see Neume for structure)
        """
        parsed_neume_components: List[NeumeComponent] = []
        for neume_comp in neume_components:
            parsed_neume_component: Optional[NeumeComponent] = (
                self._parse_neume_component(neume_comp)
            )
            if parsed_neume_component:
                parsed_neume_components.append(parsed_neume_component)
        neume_type, intervals, contours = analyze_neume(parsed_neume_components)
        # If the first neume component of the next syllable can be parsed,
        # add the interval and contour between the final neume component of
        # the current syllable and the first neume component of the next syllable.
        if next_neume_component is not None:
            parsed_next_neume_comp: Optional[NeumeComponent] = (
                self._parse_neume_component(next_neume_component)
            )
            if parsed_next_neume_comp:
                last_neume_comp = parsed_neume_components[-1]
                intervals.append(
                    get_interval_between_neume_components(
                        last_neume_comp, parsed_next_neume_comp
                    )
                )
            contours.append(get_contour_from_interval(intervals[-1]))
        parsed_neume: Neume = {
            "neume_type": neume_type,
            "neume_components": parsed_neume_components,
            "intervals": intervals,
            "contours": contours,
        }
        return parsed_neume

    def _neume_iterator(
        self,
        neumes: List[ET.Element],
        next_syllable_1st_nc: Optional[ET.Element],
    ) -> Iterator[Tuple[List[ET.Element], Optional[ET.Element]]]:
        """
        Convenience generator for iterating over a syllable's neumes.
        At each iteration step, the generator provides the 'nc' elements
        of the current neume and the first 'nc' element of the next neume
        (if it exists) so that the interval and contour between the final
        neume of the current syllable and the first neume of the next syllable
        can be computed.

        :param neumes: A list of 'neume' elements in a syllable
        :param next_syllable_1st_nc: The first 'nc' element of the next syllable

        The generator yields a tuple of:
            - The 'nc' elements of the current neume
            - The first 'nc' element of the next neume (if it exists)
        """
        neume_iterator = iter(neumes)
        current_neume = next(neume_iterator, None)
        while current_neume:
            neume_components = current_neume.findall(f"{self.MEINS}nc")
            next_neume = next(neume_iterator, None)
            if next_neume:
                next_neume_component = next_neume.find(f"{self.MEINS}nc")
            else:
                next_neume_component = next_syllable_1st_nc
            yield neume_components, next_neume_component
            current_neume = next_neume

    def _syllable_iterator(
        self,
    ) -> Iterator[Tuple[Optional[ET.Element], List[ET.Element], Optional[ET.Element]]]:
        """
        Convenience generator for iterating over syllables in an MEI file. At each
        iteration step, the generator provides all data for the current syllable
        and the first neume of the next syllable (if it exists) so that the interval
        and contour between the final neume of the current syllable and the first
        neume of the next syllable can be computed.

        The generator yields a tuple of:
            - The 'syl' element of the current syllable (containing text information),
                if it exists.
            - A list of 'neume' elements for the current syllable (containing musical
                information), if they exist.
            - The first 'nc' element (neume component) of the next syllable (if it exists).
                If there is no next syllable, this value is None.
        """
        syllable_iterator = self.mei.iter(f"{self.MEINS}syllable")
        current_syllable = next(syllable_iterator, None)
        while current_syllable:
            current_syl = current_syllable.find(f"{self.MEINS}syl")
            current_neumes = current_syllable.findall(f"{self.MEINS}neume")
            next_syllable = next(syllable_iterator, None)
            next_neume = (
                next_syllable.find(f"{self.MEINS}neume") if next_syllable else None
            )
            next_nc = next_neume.find(f"{self.MEINS}nc") if next_neume else None
            yield current_syl, current_neumes, next_nc
            current_syllable = next_syllable

    def parse_mei(self) -> List[Syllable]:
        """
        Parses the MEI file into a list of syllables.

        :return: A list of syllables
        """
        syllables: List[Syllable] = []
        for text_elem, syllable_neumes, next_neume_comp in self._syllable_iterator():
            syllable_text: SyllableText = self._parse_syllable_text(text_elem)
            neumes_list: List[Neume] = []
            for neume, next_neume_1st_nc in self._neume_iterator(
                syllable_neumes, next_neume_comp
            ):
                neumes_list.append(self._parse_neume(neume, next_neume_1st_nc))
            syllable_dict: Syllable = {
                "text": syllable_text,
                "neumes": neumes_list,
            }
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


def get_contour_from_interval(interval: int) -> ContourType:
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


def analyze_neume(
    neume: List[NeumeComponent],
) -> Tuple[str, List[int], List[ContourType]]:
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
    contours: List[ContourType] = [get_contour_from_interval(i) for i in intervals]
    neume_type: str = NEUME_GROUPS.get("".join(contours), "Compound")
    return neume_type, intervals, contours
