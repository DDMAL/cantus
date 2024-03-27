"""
Contains type definitions used in the MEI parsing process.
"""

from typing import Tuple, TypedDict, Literal, List, Optional
from typing_extensions import TypeAlias

# A type for coordinates of bounding boxes
CoordinatesType: TypeAlias = Tuple[int, int, int, int]
"""
A type for coordinates of bounding boxes. The coordinates
of the box are given as four integers designating, in order:
    - the x-coordinate of the upper-left corner of the box ("ulx")
    - the y-coordinate of the upper-left corner of the box ("uly")
    - the x-coordinate of the lower-right corner of the box ("lrx")
    - the y-coordinate of the lower-right corner of the box ("lry")
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


ContourType = Literal["u", "d", "s"]


class NeumeComponentElementData(TypedDict):
    """
    A type containing information extracted from
    an MEI neume component element.


    pname: The pitch name of the neume component (ie. "c", "d", "e", etc.)
    octave: The octave of the neume component (as an integer, in scientific
        pitch notation; e.g. middle c has octave "4")
    bounding_box: The bounding box of the neume component
    """

    pname: str
    octave: int
    bounding_box: Zone


class NeumeComponent(NeumeComponentElementData):
    """A type extending NeumeComponentElementData with interval and contour information.


    interval: The interval (in semitones) between the neume component and the
        following neume component. If there is no following neume component,
        this is None.
    contour: The contour ("u"[p], "d"[own], or "s"[tay]) of 'interval'. If there is no
        following neume component, this is None.
    """

    interval: Optional[int]
    contour: Optional[ContourType]


class Neume(TypedDict):
    """A type for neumes

    neume_type: The name of the neume (ie. "Punctum", "Pes", "Clivis", etc.)
    neume_components: A list of neume components (containing pitch infomation)
    bounding_box: The bounding box of the neume
    system: The system number that the neume is on
    """

    neume_type: str
    neume_components: List[NeumeComponent]
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
