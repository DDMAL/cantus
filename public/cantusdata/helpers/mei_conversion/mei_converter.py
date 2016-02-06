import uuid

from .abstract_mei_converter import AbstractMEIConverter, getNeumeNames
from .location_utils import getLocation
from .pitch_utils import getPitches, getContour, getIntervals


class MEIConverter (AbstractMEIConverter):
    def process(self):
        for doc in self._get_pitch_sequences():
            yield doc

        if self.min_gram > 1:
            for doc in self._get_short_neumes():
                yield doc

    def _get_pitch_sequences(self):
        notes = self.doc.getElementsByName('note')
        note_count = len(notes)

        for i in range(self.min_gram, self.max_gram + 1):
            print "Processing pitch sequences... "

            for j in range(0, note_count - i):
                yield self._process_sequence(notes[j:j + i])

    def _process_sequence(self, seq):
        neume_elems = _get_distinct_neume_elems(seq)
        neume_names = getNeumeNames(neume_elems)

        pnames, midipitch = getPitches(seq)

        semitones = [m - n for n, m in
                     zip(midipitch[:-1], midipitch[1:])]

        str_semitones = '_'.join(str(s) for s in semitones[1:-1])

        intervals = getIntervals(semitones, pnames)
        contour = getContour(semitones)

        location = getLocation(seq, self.cache, get_neume=_get_neume_elem)

        return {
            'id': str(uuid.uuid4()),
            'type': self.TYPE,
            'siglum_slug': self.siglum_slug,
            'folio': self.page_number,
            'pnames': pnames,
            'neumes': neume_names,
            'contour': contour,
            'semitones': str_semitones,
            'intervals': intervals,
            'location': str(location)
        }

    def _get_short_neumes(self):
        """Extract single neumes whose note sequences are too short to be ngrams.

        Usually it is possible to do single neume search using the records
        created for note sequences. However, neumes whose note sequences are too
        short will only be indexed along with adjacent neumes. To be able to index
        them for single neume search we need to add them separately.
        """
        for neume in self.doc.getElementsByName('neume'):
            notes = neume.getDescendantsByName('note')

            if len(notes) < self.min_gram:
                location = getLocation(notes, self.cache, get_neume=_get_neume_elem)

                yield {
                    'id': str(uuid.uuid4()),
                    'type': "cantusdata_music_notation",
                    'siglum_slug': self.siglum_slug,
                    'folio': self.page_number,
                    'neumes': str(neume.getAttribute('name').value),
                    'location': str(location)
                }


def _get_distinct_neume_elems(notes):
    neume_elems = []

    for note in notes:
        neume_elem = _get_neume_elem(note)

        if not neume_elems or neume_elem.id != neume_elems[-1].id:
            neume_elems.append(neume_elem)

    return neume_elems


def _get_neume_elem(note_elem):
    # FIXME(wabain): This is quite fragile
    return note_elem.parent.parent
