"""
Defines a class MEITokenizer that extends MEIParser with functionaliy
used to create json documents from an MEI file. These json documents
can then be indexed by a search engine (i.e. for this project, Solr). 
"""

from typing import List, Iterator, Any, TypedDict, Literal
from .mei_parser import MEIParser
from .mei_parsing_types import ContourType


class MusicalSequencesDict(TypedDict):
    """
    Type definition for a dictionary containing a sequence of musical data.
    """

    neume_names: List[str]
    pitch_names: List[str]
    intervals: List[str]
    contours: List[ContourType]


class NgramDocument(TypedDict):
    id: str
    type: str
    location: str


class NeumeNamesNgramDocument(NgramDocument):
    neume_names: str


class PitchNamesNgramDocument(NgramDocument):
    pitch_names: str


class IntervalsNgramDocument(NgramDocument):
    intervals: str


class ContoursNgramDocument(NgramDocument):
    contours: str


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

    """

    def __init__(
        self, mei_file: str, min_neume_ngram: int, max_neume_ngram: int
    ) -> None:
        super().__init__(mei_file)
        self.min_neume_ngram = min_neume_ngram
        self.max_neume_ngram = max_neume_ngram
        self.sequences = self._get_musical_sequences()

    def _get_musical_sequences(self) -> MusicalSequencesDict:
        """
        Get sequences of musical data from the entire MEI file.

        :return: A dictionary containing the following sequences of
            musical data (all sequences in the form of lists of strings):
            - "neume_names": A list of neume names in the file.
            - "pitch_names": A list of pitch names in the file.
            - "intervals": A list of intervals in the file.
            - "contours": A list of contours in the file.
            - "semitones": A list of semitones in the file.
        """
        neume_names = []
        pitch_names = []
        intervals = []
        contours = []
        for syllable in self.syllables:
            for neume in syllable["neumes"]:
                neume_names.append(neume["neume_type"])
                contours.extend(neume["contours"])
                intervals.extend([str(interval) for interval in neume["intervals"]])
                for component in neume["neume_components"]:
                    pitch_names.append(component["pname"] + str(component["octave"]))
        return {
            "neume_names": neume_names,
            "pitch_names": pitch_names,
            "intervals": intervals,
            "contours": contours,
        }

    def _get_ngrams(
        self, ngram_type: Literal["neume_names", "pitch_names", "intervals", "contours"]
    ) -> List[str]:
        """
        Get n-grams of a particular type from the MEI file.

        :param ngram_type: The type of n-gram to generate. Must be one of
            "neume_names", "pitch_names", "intervals", or "contours".
        :return: A list of n-grams represented as strings of space-separated
            items of the specified type.
        """
        return [
            " ".join(ngram)
            for ngram in generate_ngrams(
                self.sequences[ngram_type],
                self.min_neume_ngram,
                self.max_neume_ngram,
            )
        ]
