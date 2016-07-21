from itertools import groupby

import uuid

from .abstract_mei_converter import AbstractMEIConverter
from .mei_tokens import NeumeToken
from .location_utils import getLocation
from .pitch_utils import getPitches, getContour, getIntervals


class MEIConverter (AbstractMEIConverter):
    def process(self):
        notes = []

        standalone_neumes = []

        for neume in NeumeToken.get_all_from_doc(self.doc):
            neume_notes = list(neume.get_notes())

            if len(neume_notes) < self.min_gram:
                standalone_neumes.append(neume)

            notes.extend(neume_notes)

        for doc in self._get_note_ngrams(notes):
            yield doc

        for neume in standalone_neumes:
            yield self._get_neume_ngram(neume)

    def _get_note_ngrams(self, notes):
        note_count = len(notes)

        for i in range(self.min_gram, self.max_gram + 1):
            for j in range(0, note_count - i):
                yield self._get_note_ngram(notes[j:j + i])

    def _get_note_ngram(self, seq):
        neumes = _get_distinct_neumes(seq)
        neume_names = '_'.join(neume.name for neume in neumes)

        pnames, midipitch = getPitches(seq)

        semitones = [m - n for n, m in
                     zip(midipitch[:-1], midipitch[1:])]

        str_semitones = '_'.join(str(s) for s in semitones)

        intervals = getIntervals(semitones, pnames)
        contour = getContour(semitones)

        location = getLocation(neumes)

        return {
            'id': str(uuid.uuid4()),
            'type': self.TYPE,
            'siglum_slug': self.siglum_slug,
            'folio': self.page_number,
            'image_uri': self.image_uri,
            'pnames': pnames,
            'neumes': neume_names,
            'contour': contour,
            'semitones': str_semitones,
            'intervals': intervals,
            'location': str(location)
        }

    def _get_neume_ngram(self, neume):
        """Extract single neumes whose note sequences are too short to be ngrams.

        Usually it is possible to do single neume search using the records
        created for note sequences. However, neumes whose note sequences are too
        short will only be indexed along with adjacent neumes. To be able to index
        them for single neume search we need to add them separately.
        """
        location = getLocation([neume])

        return {
            'id': str(uuid.uuid4()),
            'type': self.TYPE,
            'siglum_slug': self.siglum_slug,
            'folio': self.page_number,
            'image_uri': self.image_uri,
            'neumes': neume.name,
            'location': str(location)
        }


def _get_distinct_neumes(seq):
    return [neume for (neume, _) in groupby(seq, lambda note: note.neume)]
