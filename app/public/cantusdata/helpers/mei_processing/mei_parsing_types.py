"""
Contains type definitions used in the MEI parsing process.
"""

from typing import Tuple, TypedDict, Literal, List
from typing_extensions import TypeAlias

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
    bounding_box: The bounding box of the neume
    system: The system number that the neume is on
    """

    neume_type: str
    neume_components: List[NeumeComponent]
    intervals: List[int]
    contours: List[ContourType]
    bounding_box: Zone
    system: int


class SyllableText(TypedDict):
    """A type for the text of a syllable"""

    text: str
    bounding_box: Zone


class Syllable(TypedDict):
    """A type for syllables"""

    text: SyllableText
    neumes: List[Neume]
