"""
Defines a class MEITokenizer that extends MEIParser with functionaliy
used to create json documents from an MEI file. These json documents
can then be indexed by a search engine (i.e. for this project, Solr). 
"""

import uuid
from itertools import takewhile
from typing import List, Iterator, Any, TypedDict, Literal, Tuple, Union, Sequence, cast
from typing_extensions import NotRequired
from .mei_parser import MEIParser
from .mei_parsing_types import Neume, NeumeComponent, ContourType
from .bounding_box_utils import combine_bounding_boxes, stringify_bounding_boxes


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
    intervals: A string containing the intervals between the neume components in the n-gram,
        separated by underscores.
    neume_names: A string containing the names of the neumes in the n-gram,
        separated by underscores. This field is not required, and is only present when
        the n-gram contains complete neumes.

    The following may be part of an NgramDocument, but are not required:
        manuscript_id: The ID of the manuscript the n-gram belongs to.
        folio_number: The number of the folio on which the n-gram exists.
        id: The unique ID of the document (corresponds to solr schema's id field)
        type: The type of the document (corresponds to solr schema's type field)
    """

    location: str
    pitch_names: str
    contour: str
    semitones: str
    neume_names: NotRequired[str]
    manuscript_id: NotRequired[str]
    folio: NotRequired[str]
    id: NotRequired[str]
    type: NotRequired[Literal["omr_ngram"]]
    image_uri: NotRequired[str]


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

    def _calculate_num_leading_puncta(self, neumes: List[Neume]) -> int:
        """
        Calculate the number of leading Puncta in a sequence of neumes.

        :param neumes: A list of neumes to calculate the number of leading Puncta in.
        :return: The number of leading Puncta in the sequence of neumes.
        """
        return len(list(takewhile(lambda x: x["neume_name"] == "Punctum", neumes)))

    def _stringify_ngram_pitch_data(
        self,
        ngram: Sequence[Union[Neume, NeumeComponent]],
        ngram_components: Literal["neumes", "neume_components"],
    ) -> Tuple[str, str, str]:
        """
        Convert pitch, contour, and interval information from a list of neumes
        or neume components into strings.

        :param neumes: A list of neumes or neume components to convert into strings.
        :return: A tuple containing the pitch names, contours, and intervals
            of the neumes or neume components as strings, separated by underscores.
        """
        if ngram_components == "neumes":
            neume_components: List[NeumeComponent] = []
            for neume in ngram:
                neume_components.extend(neume["neume_components"])
        else:
            neume_components = ngram
        pnames: List[str] = []
        contours: List[ContourType] = []
        intervals: List[str] = []
        for idx, neume in enumerate(neume_components):
            pnames.append(neume["pname"])
            # The interval is None if and only if the countour is None,
            # so we can safely do this single check.
            if neume["contour"] is not None and idx != len(neume_components) - 1:
                contours.append(neume["contour"])
                intervals.append(str(neume["semitones"]))
        return "_".join(pnames), "_".join(contours), "_".join(intervals)

    def get_ngram_documents(self) -> List[NgramDocument]:
        """
        Generate pitch- and neume-level n-grams from a sequence of neumes.

        This generator implements the following logic:
            - For each neume in the document, generate all possible
                n-grams (with lengths between min_ngram and max_ngram)
                that start with that neume.
            - If the current neume is a Punctum followed by m consecutive
                Puncta (where m is greater than 0), then pitch-level n-grams
                and neume-level n-grams for n = 2, 3, ..., m+1 beginning with
                the current neume are the same (because every neume in these
                n-grams corresponds to a single pitch). So, for every n = m + 1,
                ..., max_ngram, generate pitch-level n-grams
                that start with the current neume.
            - If the current neume is not a Punctum, generate pitch-level
                n-grams for n >= min_ngram and n <= max_ngram starting at
                each pitch in the current neume.

        :param sequence: A list of Neumes to generate n-grams from.
        :yield: A list containing the subset of consecutive items
            that make up an n-gram.
        """
        neume_sequence: List[Neume] = []
        for syllable in self.syllables:
            for neume in syllable["neumes"]:
                neume_sequence.append(neume)
        ngram_docs: List[NgramDocument] = []
        for start_neume_idx, current_neume in enumerate(neume_sequence):
            # Get neume-level n-grams starting at the current neume
            for n in range(self.min_ngram, self.max_ngram + 1):
                end_neume_idx = start_neume_idx + n
                if end_neume_idx > len(neume_sequence):
                    break
                neume_ngram = neume_sequence[start_neume_idx:end_neume_idx]
                pitch_names, contour, intervals = self._stringify_ngram_pitch_data(
                    neume_ngram, "neumes"
                )
                bounding_box_and_system = [
                    (neume["bounding_box"], neume["system"]) for neume in neume_ngram
                ]
                location = stringify_bounding_boxes(
                    combine_bounding_boxes(bounding_box_and_system)
                )
                ngram_docs.append(
                    {
                        "location": location,
                        "pitch_names": pitch_names,
                        "contour": contour,
                        "semitones": intervals,
                        "neume_names": "_".join(
                            neume["neume_name"] for neume in neume_ngram
                        ),
                        "id": str(uuid.uuid4()),
                        "type": "omr_ngram",
                    }
                )
            # The longest neume ngram we were able to generate starting at the
            # current neume will contain at least max_ngram pitches. We'll use
            # this neume ngram to generate pitch-level n-grams.
            longest_neume_ngram = neume_ngram
            # If the current neueme is a Punctum, the number of consecutive
            # Puncta following determines where we need to start generating
            # pitch-level n-grams. See docstring for details.
            num_leading_puncta = self._calculate_num_leading_puncta(longest_neume_ngram)
            min_pitch_ngram = max(num_leading_puncta + 1, self.min_ngram)
            # If every neume in longest_neume_ngram is a Punctum, we can skip
            # generating any additional pitch-level ngrams.
            if num_leading_puncta == self.max_ngram:
                continue
            ncs_and_systems: List[Tuple[NeumeComponent, int]] = []
            # Collect nueme components and their system
            # from the longest neume ngram
            for neume in longest_neume_ngram:
                neume_components = neume["neume_components"]
                ncs_and_systems.extend((nc, neume["system"]) for nc in neume_components)
            # Generate necessary pitch-level n-grams starting with
            # the pitches in the current neume
            num_pitches_curr_neume = len(current_neume["neume_components"])
            for start_pitch_idx in range(num_pitches_curr_neume):
                for n in range(min_pitch_ngram, self.max_ngram + 1):
                    nc_ngram_with_sys = ncs_and_systems[
                        start_pitch_idx : start_pitch_idx + n
                    ]
                    pitch_names, contour, intervals = self._stringify_ngram_pitch_data(
                        [nc for nc, _ in nc_ngram_with_sys], "neume_components"
                    )
                    bounding_box_and_system = [
                        (nc["bounding_box"], system) for nc, system in nc_ngram_with_sys
                    ]
                    location = stringify_bounding_boxes(
                        combine_bounding_boxes(bounding_box_and_system)
                    )
                    ngram_docs.append(
                        {
                            "location": location,
                            "pitch_names": pitch_names,
                            "contour": contour,
                            "semitones": intervals,
                            "id": str(uuid.uuid4()),
                            "type": "omr_ngram",
                        }
                    )
        return ngram_docs
