"""
Defines a class MEITokenizer that extends MEIParser with functionaliy
used to create json documents from an MEI file. These json documents
can then be indexed by a search engine (i.e. for this project, Solr). 
"""

import uuid
from typing import List, Tuple, Optional
from .mei_parser import MEIParser
from .mei_parsing_types import (
    Neume,
    NeumeComponent,
    ContourType,
    NeumeName,
    NgramDocument,
    Zone,
)
from .bounding_box_utils import combine_bounding_boxes, stringify_bounding_boxes


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

    @property
    def flattened_neumes(self) -> List[Neume]:
        """
        Flatten the neumes contained in the syllables of the MEI file.

        :return: A list of neumes.
        """
        neumes: List[Neume] = []
        for syllable in self.syllables:
            neumes.extend(syllable["neumes"])
        return neumes

    def _stringify_neume_component_data(
        self,
        neume_components: List[NeumeComponent],
    ) -> Tuple[str, str, str]:
        """
        Convert pitch, contour, and interval information from a list of
        neume components into strings.

        :param neume_components: A list of neumes or neume components to convert into strings.
        :return: A tuple containing the pitch names, contours, and intervals
            of the neumes or neume components as strings, separated by underscores.
        """
        pnames: List[str] = []
        contours: List[ContourType] = []
        semitone_intervals: List[str] = []
        for idx, nc in enumerate(neume_components):
            pnames.append(nc["pname"])
            # The interval is None if and only if the countour is None,
            # so we can safely do this single check.
            if nc["contour"] is not None and idx != len(neume_components) - 1:
                contours.append(nc["contour"])
                semitone_intervals.append(str(nc["semitone_interval"]))
        return "_".join(pnames), "_".join(contours), "_".join(semitone_intervals)

    def _create_document_from_neume_components(
        self,
        neume_components: List[NeumeComponent],
    ) -> NgramDocument:
        """
        Create an NgramDocument from a list of neume components and
        their corresponding system numbers.

        :param ncs_with_sys: A list of tuples, each containing a neume component
            and the system number of that neume component.
        :return: An NgramDocument containing the information from the neume components.
        """
        pitch_names, contour, intervals = self._stringify_neume_component_data(
            neume_components
        )
        zones_with_sys: List[Tuple[Zone, int]] = [
            (nc["bounding_box"], nc["system"]) for nc in neume_components
        ]
        location: str = stringify_bounding_boxes(combine_bounding_boxes(zones_with_sys))
        return {
            "location_json": location,
            "pitch_names": pitch_names,
            "contour": contour,
            "semitone_intervals": intervals,
            "id": str(uuid.uuid4()),
            "type": "omr_ngram",
        }

    def _create_pitch_sequences(
        self,
    ) -> Tuple[List[NeumeComponent], List[Optional[NeumeName]]]:
        """
        Create two lists of equal length: one containing
        the pitches (neume components) contained in the parsed file,
        and the other containing the names of the neumes that begin
        at each pitch (or None if no neume begins at that pitch).

        :return: A tuple containing the list of pitches and the list of neume names.
        """
        neume_sequence = self.flattened_neumes
        neume_names: List[Optional[NeumeName]] = []
        ncs: List[NeumeComponent] = []
        for neume in neume_sequence:
            ncs.extend(neume["neume_components"])
            flattened_neume_names = [neume["neume_name"]] + [None] * (
                len(neume["neume_components"]) - 1
            )
            neume_names.extend(flattened_neume_names)
        return ncs, neume_names

    def create_ngram_documents(self) -> List[NgramDocument]:
        """
        Create a list of ngram documents from the MEI file,
        ensuring that we have ngrams that contain n pitches
        and n neumes for all n in the range min_ngram to max_ngram.

        In broad strokes, the function:
            - Iterates through the pitches in the document, and creates ngrams
               of pitches with n = min_ngram, min_ngram + 1, ..., max_ngram.
               When an ngram corresponds to a set of complete neumes, neume
               names are included in the ngram document. When it doesn't,
               no neume names are added.
            - Checks whether this has created ngrams of length up to max_ngram
                of complete neumes starting at the current pitch.
                (Note: this will only be the case if the
                current pitch begins a sequence of max_ngram consecutive single-
                pitch neumes).
            - If this check fails, the function creates remaining ngrams of complete
                neumes up to max_ngram of complete neumes.

        :return: A list of NgramDocuments.
        """
        pitches, neume_names = self._create_pitch_sequences()
        ngram_docs: List[NgramDocument] = []
        num_pitches = len(pitches)
        # At each pitch in the file, we'll generate all the necessary
        # ngrams that start with that pitch.
        for start_idx in range(num_pitches):
            largest_num_neumes = 0
            for ngram_length in range(self.min_ngram, self.max_ngram + 1):
                # Collect the pitches for an ngram of ngram_length
                # pitches starting at start_idx, if we haven't reached the
                # end of the pitches.
                end_idx = start_idx + ngram_length
                if end_idx > num_pitches:
                    break
                nc_ngram = pitches[start_idx:end_idx]
                doc = self._create_document_from_neume_components(nc_ngram)
                # If the pitch at start_idx is the beginning of a neume
                # and the pitch following this ngram is also the beginning
                # of a neume (or we've reached the end of the file),
                # then our current ngram of pitches overlaps
                # with some number of complete neumes.
                neume_start = neume_names[start_idx] is not None
                if neume_start:
                    if end_idx == num_pitches or neume_names[end_idx] is not None:
                        neume_name_list = [
                            nn
                            for nn in neume_names[start_idx:end_idx]
                            if nn is not None
                        ]
                        doc["neume_names"] = "_".join(neume_name_list)
                        largest_num_neumes = len(neume_name_list)
                ngram_docs.append(doc)
            # If the current neume component starts a neume and we
            # haven't reached the maximum ngram length of neumes
            # in our existing documents, generate documents containing
            # larger ngrams of neumes until we reach the maximum ngram length.
            if neume_start and largest_num_neumes < self.max_ngram:
                min_wanted_ngram_length = max(largest_num_neumes + 1, self.min_ngram)
                for wanted_ngram_length in range(
                    min_wanted_ngram_length, self.max_ngram + 1
                ):
                    ngram_neume_names: List[NeumeName] = []
                    ngram_num_pitches = 0
                    # We'll add pitches to our ngram until we have the
                    # number of neumes we want in our ngram or we reach
                    # the end of the file.
                    while (len(ngram_neume_names) <= wanted_ngram_length) and (
                        start_idx + ngram_num_pitches < len(pitches)
                    ):
                        if (
                            name_at_pitch := neume_names[start_idx + ngram_num_pitches]
                        ) is not None and len(ngram_neume_names) < wanted_ngram_length:
                            ngram_neume_names.append(name_at_pitch)
                        ngram_num_pitches += 1
                        if len(ngram_neume_names) == wanted_ngram_length:
                            break
                    # We'll only add this ngram if we've actually gotten to
                    # the desired number of neumes (if we didn't, it means
                    # we reached the end of the file)
                    if len(ngram_neume_names) == wanted_ngram_length:
                        ngram_pitches = pitches[
                            start_idx : start_idx + ngram_num_pitches
                        ]
                        doc = self._create_document_from_neume_components(ngram_pitches)
                        doc["neume_names"] = "_".join(ngram_neume_names)
                        ngram_docs.append(doc)
        return ngram_docs
