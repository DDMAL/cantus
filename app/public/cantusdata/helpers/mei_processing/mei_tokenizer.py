"""
Defines a class MEITokenizer that extends MEIParser with functionaliy
used to create json documents from an MEI file. These json documents
can then be indexed by a search engine (i.e. for this project, Solr). 
"""

from typing import List, Iterator, Any, TypedDict, Literal
from typing_extensions import NotRequired
from .mei_parser import MEIParser
from .mei_parsing_types import Neume, NeumeComponent
from .bounding_box_utils import combine_bounding_boxes, stringify_bounding_boxes

NgramUnitType = Literal["neume", "neume_component"]


class NgramDocument(TypedDict):
    """
    A generic type for documents containing n-grams
    of information extracted from MEI files.

    ngram_unit: The unit of the n-gram
    location: The location of the n-gram in the MEI file (MEI Zones
        converted to JSON strings according to bounding_box_utils.stringify_bounding_boxes)

    The following may be part of an NgramDocument, but are not required:
        manuscript_id: The ID of the manuscript the n-gram belongs to.
        folio_number: The number of the folio on which the n-gram exists.
        id: The unique ID of the document (corresponds to solr schema's id field)
        type: The type of the document (corresponds to solr schema's type field)
    """

    ngram_unit: NgramUnitType
    location: str
    manuscript_id: NotRequired[str]
    folio: NotRequired[str]
    id: NotRequired[str]
    type: NotRequired[Literal["omr_ngram"]]


class NeumeNgramDocument(NgramDocument):
    """
    A type for documents containing n-grams of neume-level information.

    neume_names: A string containing the names of the neumes in the n-gram,
        separated by underscores.
    """

    neume_names: str


class NeumeComponentNgramDocument(NgramDocument):
    """
    A type for documents containing n-grams of neume component-level information.

    pitch_names: A string containing the pitch names of the neume components in the n-gram,
        separated by underscores.
    intervals: A string containing the intervals between the neume components in the n-gram,
        separated by underscores.
    contours: A string containing the contours of the neume components in the n-gram, separated
        by underscores.
    """

    pitch_names: str
    intervals: str
    contour: str


def generate_ngrams(sequence: List[Any], min_n: int, max_n: int) -> Iterator[List[Any]]:
    """
    Generate n-grams from a sequence (list) of items.

    :param sequence: A list of items to generate n-grams from.
    :param min_gram: The minimum length of n-grams to generate.
    :param max_gram: The maximum length of n-grams to generate.
    :yield: A list containing the subset of consecutive items
        that make up an n-gram.
    """
    # Iterate through all desired n-gram lengths
    for i in range(min_n, max_n + 1):
        # Iterate through all n-grams of "sequence" of length "i"
        for j in range(0, len(sequence) - i + 1):
            yield sequence[j : j + i]


class MEITokenizer(MEIParser):
    """
    An MEITokenizer object is initialized with an MEI file and a set of
    parameters that define how the MEI file should be tokenized. These
    parameters are:
    - min_ngram: The minimum length of n-grams to generate.
    - max_ngram: The maximum length of n-grams to generate.
    """

    def __init__(self, mei_file: str, min_ngram: int, max_ngram: int) -> None:
        super().__init__(mei_file)
        self.min_ngram = min_ngram
        self.max_ngram = max_ngram

    def get_neume_ngram_docs(self) -> List[NeumeNgramDocument]:
        """
        Generate neume-level documents for search, containing
        n-grams of neume names.

        :return: A list of dictionaries containing the n-grams
            of neume names.
        """
        neumes_sequence: List[Neume] = []
        for syllable in self.syllables:
            neumes_sequence.extend(syllable["neumes"])
        neume_documents: List[NeumeNgramDocument] = []
        for ngram in generate_ngrams(neumes_sequence, self.min_ngram, self.max_ngram):
            bounding_boxes = [
                (neume["bounding_box"], neume["system"]) for neume in ngram
            ]
            document_location = combine_bounding_boxes(bounding_boxes)
            neume_names = "_".join([neume["neume_type"] for neume in ngram])
            neume_documents.append(
                {
                    "ngram_unit": "neume",
                    "location": stringify_bounding_boxes(document_location),
                    "neume_names": neume_names,
                }
            )
        return neume_documents

    def get_neume_component_ngram_docs(self) -> List[NeumeComponentNgramDocument]:
        """
        Generate neume component-level documents for search, containing
        n-grams of pitch names, intervals, and contours.

        :return: A list of dictionaries containing the n-grams
            of pitch names, intervals, and contours.
        """
        neume_components: List[NeumeComponent] = []
        for syllable in self.syllables:
            for neume in syllable["neumes"]:
                neume_components.extend(neume["neume_components"])
        neume_component_documents: List[NeumeComponentNgramDocument] = []
        for ngram in generate_ngrams(
            neume_components,
            self.min_ngram,
            self.max_ngram,
        ):
            pitch_names = "_".join([comp["pname"] for comp in ngram])
            # Keep "internal" intervals and contours (in other words,
            # the intevals and countours between the pitches in these
            # neume components, and not the interval and contour following
            # the last pitch in the ngram).
            intervals = [str(comp["interval"]) for comp in ngram[:-1]]
            contour = [comp["contour"] for comp in ngram[:-1]]
            bounding_boxes = [(comp["bounding_box"], neume["system"]) for comp in ngram]
            document_location = combine_bounding_boxes(bounding_boxes)
            neume_component_documents.append(
                {
                    "ngram_unit": "neume_component",
                    "location": stringify_bounding_boxes(document_location),
                    "pitch_names": pitch_names,
                    "intervals": "_".join(intervals),
                    "contour": "_".join(contour),
                }
            )
        return neume_component_documents
