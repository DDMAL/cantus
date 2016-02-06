import uuid

from .abstract_mei_converter import AbstractMEIConverter, getNeumeNames
from .location_utils import getLocation
from .pitch_utils import getPitchNames, getContour, getIntervals


class MEIConverter (AbstractMEIConverter):
    def process(self):
        docs = self.getPitchSequences()

        if self.min_gram > 1:
            docs.extend(self.getShortNeumes())

        return docs

    def getPitchSequences(self):
        """Extract ngrams for note sequences from the MEI file"""
        notes = self.doc.getElementsByName('note')
        nnotes = len(notes)  # number of notes in file

        mydocs = []

        for i in range(self.min_gram, self.max_gram + 1):

            #*******************TEST************************
            # for note in notes:
            #             s = meifile.get_system(note)
            #             neume = str(note.parent.parent.attribute_by_name('name').value)
            #             print 'pitch: '+ str(note.pitch[0])+ ' neume: ' + neume + " system: " +str(s)
            #***********************************************

            print "Processing pitch sequences... "
            # for j,note in enumerate(notes):
            for j in range(0, nnotes - i):
                seq = notes[j:j + i]

                location = getLocation(seq, self.cache, get_neume=getNeumeElem)

                # get neumes
                neume_elems = []

                for note in seq:
                    neume_elem = getNeumeElem(note)

                    if not neume_elems or neume_elem.id != neume_elems[-1].id:
                        neume_elems.append(neume_elem)

                neume_names = getNeumeNames(neume_elems)

                # get pitch names
                [pnames, midipitch] = getPitchNames(seq)

                # get semitones
                # calculate difference between each adjacent entry in midipitch list
                semitones = [m - n for n, m in
                             zip(midipitch[:-1], midipitch[1:])]
                str_semitones = str(semitones)[
                                1:-1]  # string will be stored instead of array for easy searching
                str_semitones = str_semitones.replace(', ', '_')

                # get quality invariant interval name and direction
                # for example, an ascending major second and an ascending
                # minor second will both be encoded as 'u2'

                # the only tritone to occur would be between b and f, in the
                #  context of this application we will assume that the be
                # will always be sung as b flat

                # thus the tritone is never encoded as such and will always
                # be represented as either a fifth or a fourth, depending
                # on inversion
                intervals = getIntervals(semitones, pnames)

                # get contour - encode with Parsons code for musical contour
                contour = getContour(semitones)

                # save new document
                mydocs.append(
                        {
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
                )

        return mydocs

    def getShortNeumes(self):
        """Extract single neumes whose note sequences are too short to be ngrams.

        Usually it is possible to do single neume search using the records
        created for note sequences. However, neumes whose note sequences are too
        short will only be indexed along with adjacent neumes. To be able to index
        them for single neume search we need to add them separately.
        """
        neume_docs = []

        for neume in self.doc.getElementsByName('neume'):
            notes = neume.getDescendantsByName('note')

            if len(notes) < self.min_gram:
                location = getLocation(notes, self.cache, get_neume=getNeumeElem)

                neume_docs.append({
                    'id': str(uuid.uuid4()),
                    'type': "cantusdata_music_notation",
                    'siglum_slug': self.siglum_slug,
                    'folio': self.page_number,
                    'neumes': str(neume.getAttribute('name').value),
                    'location': str(location)
                })

        return neume_docs


def getNeumeElem(note_elem):
    # FIXME(wabain): This is quite fragile
    return note_elem.parent.parent
