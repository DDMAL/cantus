"""
Contains type definitions used in the MEI parsing process.
"""

from typing import Tuple, TypedDict, Literal, List, Optional, NotRequired
from typing_extensions import TypeAlias

from cantusdata.helpers.neume_helpers import NeumeName

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


ContourType = Literal["u", "d", "r"]


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


    semitone_interval: The interval in semitones between the neume component and the
        following neume component. If there is no following neume component,
        this is None.
    contour: The contour ("u"[p], "d"[own], or "r"[epeat]) of 'interval'. If there is no
        following neume component, this is None.
    interval: The interval (2nd, 5th, etc) between the neume component and the following
        neume component. If there is no following neume component, this is None.
    system: The system number that the neume component is on
    """

    semitone_interval: Optional[int]
    contour: Optional[ContourType]
    interval: Optional[int]
    system: int


class Neume(TypedDict):
    """A type for neumes

    neume_name: The name of the neume (ie. "punctum", "pes", "clivis", etc.)
    neume_components: A list of neume components (containing pitch infomation)
    bounding_box: The bounding box of the neume
    system: The system number that the neume is on
    """

    neume_name: NeumeName
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


class NgramDocument(TypedDict):
    """
    A generic type for documents containing n-grams
    of information extracted from MEI files.

    ngram_unit: The unit of the n-gram
    location: The location of the n-gram in the MEI file (MEI Zones
        converted to JSON strings according to bounding_box_utils.stringify_bounding_boxes)
    pitch_names: A string containing the pitch names of the neume components in the n-gram,
        separated by underscores.
    contour: A string containing the contours of the neume components in the n-gram, separated
        by underscores.
    semitone_interval: A string containing the semitone intervals between the neume components
        in the n-gram, separated by underscores.
    intervals: A string containing the intervals between the neume components in the n-gram,
        separated by underscores.
    neume_names: A string containing the names of the neumes in the n-gram,
        separated by underscores. This field is not required, and is only present when
        the n-gram contains complete neumes.

    The following may be part of an NgramDocument, but are optional because
    they will be added when the document is indexed:
        manuscript_id: The ID of the manuscript the n-gram belongs to.
        folio_number: The number of the folio on which the n-gram exists.
        id: The unique ID of the document (corresponds to solr schema's id field)
        type: The type of the document (corresponds to solr schema's type field)
    """

    location_json: str
    pitch_names: str
    contour: str
    semitone_intervals: str
    intervals: str
    neume_names: NotRequired[str]
    manuscript_id: NotRequired[str]
    folio: NotRequired[str]
    id: NotRequired[str]
    type: NotRequired[Literal["omr_ngram"]]
    image_uri: NotRequired[str]
