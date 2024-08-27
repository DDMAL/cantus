"""
Defines a class, MEIParser, that converts the contents of an MEI file into 
python types for ease of subsequent processing. 

Also defines some additional functions useful for analyzing contents of an MEI
file:
    - get_interval_between_neume_components: Computes the interval (in semitones)
        between two neume components.
    - get_contour_from_interval: Computes the contour of an interval.
    - analyze_neume: Analyzes a neume (a list of neume components) to determine its
        neume name, its intervals, and its contour.

Defines associated types for the data structures used by the parser.
"""

from typing import Tuple, Dict, List, Iterator, Optional, Literal
from lxml import etree  # pylint: disable=no-name-in-module
from .mei_parsing_types import (
    Zone,
    SyllableText,
    NeumeComponentElementData,
    NeumeComponent,
    ContourType,
    NeumeName,
    Neume,
    Syllable,
)
from .bounding_box_utils import combine_bounding_boxes_single_system

# Mapping from pitch names to integer pitch class where C = 0
PITCH_CLASS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

# Mapping from neume contours to neume names
NEUME_GROUPS: Dict[str, NeumeName] = {
    "": "punctum",
    "u": "pes",
    "d": "clivis",
    "uu": "scandicus",
    "ud": "torculus",
    "du": "porrectus",
    "r": "distropha",
    "rr": "tristopha",
    "rd": "pressus",
    "dd": "climacus",
    "ddu": "climacus-resupinus",
    "udu": "torculus-resupinus",
    "dud": "porrectus-flexus",
    "udd": "pes-subpunctis",
    "uud": "scandicus-flexus",
    "uudd": "scandicus-subpunctis",
    "dudd": "porrectus-subpunctis",
}


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
        self.mei = etree.parse(self.mei_file)
        self._remove_empty_neumes_and_syllables()
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

    def _get_element_zone(self, element: etree._Element) -> Zone:
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

    def _parse_syllable_text(self, syl_elem: Optional[etree.Element]) -> SyllableText:
        """
        Get the text of a syllable and its associated bounding box from
        a 'syl' element.

        :param syllable: A syllable element from an MEI file
        :return: Dictionary of syllable text data
        """
        # Ignoring type of next two expressions because for some reason
        # mypy thinks they are unreachable, but we know they are not.
        if syl_elem is not None and syl_elem.text:  # type: ignore
            text_dict: SyllableText = {  # type: ignore
                "text": syl_elem.text.strip(),
                "bounding_box": self._get_element_zone(syl_elem),
            }
        else:
            text_dict = {
                "text": "",
                "bounding_box": {"coordinates": (-1, -1, -1, -1), "rotate": 0.0},
            }
        return text_dict

    def _parse_neume_component_element(
        self, neume_comp: etree._Element
    ) -> Optional[NeumeComponentElementData]:
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
        neume_components: List[etree._Element],
        neume_system: int,
        next_neume_component: Optional[etree._Element],
    ) -> Neume:
        """
        Gets a Neume dictionary from a series of 'nc' elements (including
        the first neume component of the following neume, if it exists)

        :param neume_components: A list of 'nc' elements in a given 'neume' element
        :param neume_system: The system number that the neume is on
        :param next_neume_component: The first 'nc' element of the next neume
        :return: A list of neume dictionaries (see Neume for structure)
        """
        parsed_nc_elements: List[NeumeComponentElementData] = []
        for neume_comp in neume_components:
            parsed_neume_component: Optional[NeumeComponentElementData] = (
                self._parse_neume_component_element(neume_comp)
            )
            if parsed_neume_component:
                parsed_nc_elements.append(parsed_neume_component)
        neume_name, semitone_intervals, contours, intervals = analyze_neume(
            parsed_nc_elements
        )
        # If the first neume component of the next syllable can be parsed,
        # add intervals and contour between the final neume component of
        # the current syllable and the first neume component of the next syllable.
        if next_neume_component is not None:
            parsed_next_neume_comp: Optional[NeumeComponentElementData] = (
                self._parse_neume_component_element(next_neume_component)
            )
            if parsed_next_neume_comp:
                last_neume_comp = parsed_nc_elements[-1]
                semitone_intervals.append(
                    get_semitones_between_neume_components(
                        last_neume_comp, parsed_next_neume_comp
                    )
                )
                contours.append(get_contour_from_interval(semitone_intervals[-1]))
                intervals.append(
                    get_melodic_interval(
                        semitone_intervals[-1], last_neume_comp["pname"]
                    )
                )
        # Get a bounding box for the neume by combining bounding boxes of
        # its components. Note that a single neume does not span multiple
        # systems, so the combined bounding box will be a single zone.
        nc_zones = [nc["bounding_box"] for nc in parsed_nc_elements]
        combined_bounding_box = combine_bounding_boxes_single_system(nc_zones)
        # Add interval and countour information to neume components
        parsed_neume_components: List[NeumeComponent] = []
        for i, nc in enumerate(parsed_nc_elements):
            parsed_neume_components.append(
                {
                    "pname": nc["pname"],
                    "octave": nc["octave"],
                    "bounding_box": nc["bounding_box"],
                    "semitone_interval": (
                        semitone_intervals[i] if i < len(semitone_intervals) else None
                    ),
                    "contour": contours[i] if i < len(contours) else None,
                    "interval": intervals[i] if i < len(intervals) else None,
                    "system": neume_system,
                }
            )
        parsed_neume: Neume = {
            "neume_name": neume_name,
            "neume_components": parsed_neume_components,
            "bounding_box": combined_bounding_box,
            "system": neume_system,
        }
        return parsed_neume

    def _neume_iterator(
        self,
        neumes: List[Tuple[etree._Element, int]],
        next_syllable_1st_nc: Optional[etree._Element],
    ) -> Iterator[Tuple[List[etree._Element], int, Optional[etree._Element]]]:
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
            current_neume_elem = current_neume[0]
            current_neume_system = current_neume[1]
            neume_components = current_neume_elem.findall(f"{self.MEINS}nc")
            next_neume = next(neume_iterator, None)
            if next_neume:
                next_neume_elem = next_neume[0]
                next_neume_component = next_neume_elem.find(f"{self.MEINS}nc")
            else:
                next_neume_component = next_syllable_1st_nc
            yield neume_components, current_neume_system, next_neume_component
            current_neume = next_neume

    def _syllable_iterator(
        self,
    ) -> Iterator[
        Tuple[
            Optional[etree._Element],
            List[Tuple[etree._Element, int]],
            Optional[etree._Element],
        ]
    ]:
        """
        Convenience generator for iterating over syllables in an MEI file. At each
        iteration step, the generator provides all data for the current syllable
        and the first neume of the next syllable (if it exists) so that the interval
        and contour between the final neume of the current syllable and the first
        neume of the next syllable can be computed.

        The generator yields a tuple of:
            - The 'syl' element of the current syllable (containing text information),
                if it exists.
            - A list of 'neume' tuples, each containing:
                - The 'neume' element of the current neume.
                - The system number that the neume is on.
            - The first 'nc' element (neume component) of the next syllable (if it exists).
                If there is no next syllable, this value is None.
        """
        system = 1
        # Find the first syllable in the file, and iterate through
        # all its 'syllable' and 'sb' siblings.
        first_syllable = self.mei.find(f".//{self.MEINS}syllable")
        if first_syllable is not None:
            elem_iterator = first_syllable.itersiblings(
                tag=[f"{self.MEINS}syllable", f"{self.MEINS}sb"]
            )
            current_elem = first_syllable
            while current_elem is not None:
                if current_elem.tag == f"{self.MEINS}syllable":
                    current_syl = current_elem.find(f"{self.MEINS}syl")
                    syllable_neumes_list: List[Tuple[etree._Element, int]] = []
                    # Iterate through the syllable's neumes and any
                    # sb tags that may be contained by the syllable.
                    # If an sb tag, increment
                    # the system counter.
                    # If a neume, add it to the list of syllable neumes
                    # to pass out of the iterator.
                    neume_sb_iterator = current_elem.iter(
                        f"{self.MEINS}neume", f"{self.MEINS}sb"
                    )
                    for neume_or_sb_elem in neume_sb_iterator:
                        if neume_or_sb_elem.tag == f"{self.MEINS}sb":
                            system += 1
                        else:
                            syllable_neumes_list.append((neume_or_sb_elem, system))
                    next_syllable = next(
                        current_elem.itersiblings(tag=f"{self.MEINS}syllable"), None
                    )
                    next_nc = None
                    if next_syllable is not None:
                        next_neume = next_syllable.find(f"{self.MEINS}neume")
                        if next_neume is not None:
                            next_nc = next_neume.find(f"{self.MEINS}nc")
                    yield current_syl, syllable_neumes_list, next_nc
                elif current_elem.tag == f"{self.MEINS}sb":
                    system += 1
                current_elem = next(elem_iterator, None)

    def _remove_empty_neumes_and_syllables(self) -> None:
        """
        Apparently, for a while Rodan was creating invalid MEI files that
        contained empty neumes (i.e., neumes with no neume components) and
        empty syllables (i.e., syllables with no neumes or only empty neumes).
        This method removes those empty neumes and syllables from the MEI being parsed;
        it was added as a preprocessing step so that it can, once the base
        MEI files are corrected, be removed.
        """
        for neume in self.mei.iter(f"{self.MEINS}neume"):
            if len(neume.findall(f"{self.MEINS}nc")) == 0:
                # Ignoring type because we know that getparent() will
                # return an element in this case.
                neume.getparent().remove(neume)  # type: ignore
        for syllable in self.mei.iter(f"{self.MEINS}syllable"):
            if len(syllable.findall(f"{self.MEINS}neume")) == 0:
                # Ignoring type because we know that getparent() will
                # return an element in this case.
                syllable.getparent().remove(syllable)  # type: ignore

    def parse_mei(self) -> List[Syllable]:
        """
        Parses the MEI file into a list of syllables.

        :return: A list of syllables
        """
        syllables: List[Syllable] = []
        for (
            text_elem,
            syllable_neumes,
            next_neume_comp,
        ) in self._syllable_iterator():
            syllable_text: SyllableText = self._parse_syllable_text(text_elem)
            neumes_list: List[Neume] = []
            for neume, neume_system, next_neume_1st_nc in self._neume_iterator(
                syllable_neumes, next_neume_comp
            ):
                neumes_list.append(
                    self._parse_neume(neume, neume_system, next_neume_1st_nc)
                )
            syllable_dict: Syllable = {
                "text": syllable_text,
                "neumes": neumes_list,
            }
            syllables.append(syllable_dict)
        return syllables


def get_semitones_between_neume_components(
    neume_component_1: NeumeComponentElementData,
    neume_component_2: NeumeComponentElementData,
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
    try:
        pc1 = PITCH_CLASS[neume_component_1["pname"]]
        pc2 = PITCH_CLASS[neume_component_2["pname"]]
    except KeyError as err:
        raise ValueError("Invalid pitch name in neume component.") from err
    # In MIDI note numbers, C0 = 12.
    pitch_1 = pc1 + (12 * (neume_component_1["octave"] + 1))
    pitch_2 = pc2 + (12 * (neume_component_2["octave"] + 1))
    return pitch_2 - pitch_1


def get_contour_from_interval(interval: int) -> ContourType:
    """
    Compute the contour of an interval.

    :param interval: The size of the interval in semitones or steps
    :return: The contour of the interval ("u"[p], "d"[own], or "r"[epeat])
    """
    if interval < 0:
        return "d"
    if interval > 0:
        return "u"
    return "r"


INTERVAL_TO_STEP_MAP: Dict[int, int] = {
    0: 1,  # unison
    1: 2,  # minor 2nd
    2: 2,  # major 2nd
    3: 3,  # minor 3rd
    4: 3,  # major 3rd
    5: 4,  # perfect 4th
    # we handle 6 semitones separately below
    # b/c we'll treat it as a 4th or 5th depending
    # on the starting pitch and direction of the interval
    7: 5,  # perfect 5th
    8: 6,  # minor 6th
    9: 6,  # major 6th
    10: 7,  # minor 7th
    11: 7,  # major 7th
}


def get_melodic_interval(semitone_interval: int, starting_pitch_name: str) -> int:
    """
    Uses the semitone size of an interval and the starting pitch
    name to determine the size of a melodic interval.
    In most cases, the interval is determined by the number of
    semitones between the pitches. However, in the case of a 6-semitone
    interval, the interval is determined by the starting pitch name
    and the contour of the interval.

    :param semitone_interval: The size of the interval in semitones
    :param starting_pitch_name: The pitch name of the starting pitch

    :return: A integer representing the size of the interval in steps,
        a positive integer for an ascending interval and a negative
        integer for a descending interval.
    """
    if semitone_interval == 0:
        return 1
    interval_magnitude = abs(semitone_interval)
    interval_direction = semitone_interval // interval_magnitude
    interval_octaves = interval_magnitude // 12
    interval_mod_12 = interval_magnitude % 12
    interval: int
    if interval_mod_12 == 6:
        # Note: Since we don't currently handle any accidentals,
        # intervals between b's and f's are the only place we'll
        # see a 6-semitone interval.
        match (starting_pitch_name, interval_direction > 0):
            case ("b", True):  # b up to f is a 5th
                interval = 5
            case ("b", False):  # b down to f is a 4th
                interval = 4
            case ("f", True):  # f up to b is a 4th
                interval = 4
            case ("f", False):  # f down to b is a 5th
                interval = 5
    else:
        interval = INTERVAL_TO_STEP_MAP[interval_mod_12]
    return (interval + 7 * interval_octaves) * interval_direction


def analyze_neume(
    neume: List[NeumeComponentElementData],
) -> Tuple[NeumeName, List[int], List[ContourType], List[int]]:
    """
    Analyze a neume (a list of neume components) to determine:
    - The neume type (e.g., punctum, pes, clivis, etc.)
    - The intervals in the neume in semitones
    - The contour of the nueme
    - The intervals in the neume in steps ("3rd", "4th")

    :param neume: A list of neume components (a list of NeumeComponentsType dictionaries)
    :return: A tuple of information about the neume:
                - Neume type (str)
                - Neume intervals in semitones (list of ints)
                - Neume contour (list of "u"[p], "d"[own], or "r"[epeat])
                - Neume intervals in steps (list of ints)
    """
    semitone_intervals: List[int] = [
        get_semitones_between_neume_components(nc1, nc2)
        for nc1, nc2 in zip(neume[:-1], neume[1:])
    ]
    contours: List[ContourType] = [
        get_contour_from_interval(i) for i in semitone_intervals
    ]
    intervals: List[int] = [
        get_melodic_interval(i, nc["pname"]) for i, nc in zip(semitone_intervals, neume)
    ]
    neume_type: NeumeName = NEUME_GROUPS.get("".join(contours), "compound")
    return neume_type, semitone_intervals, contours, intervals
