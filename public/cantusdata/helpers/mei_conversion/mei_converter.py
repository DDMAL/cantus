import uuid

from .abstract_mei_converter import AbstractMEIConverter


class MEIConverter (AbstractMEIConverter):
    def getNeumes(self, seq, counter):
        return AbstractMEIConverter.getNeumes(self, seq, counter)

    def getLocation(self, seq, meifile, zones):
        return AbstractMEIConverter.getLocation(self, seq, meifile, zones)

    def getNgramDocuments(self, mei_doc, page_number):
        zones = mei_doc.getElementsByName('zone')

        docs = self.getPitchSequences(page_number, mei_doc, zones)

        if self.min_gram > 1:
            docs.extend(self.getShortNeumes(page_number, mei_doc, zones))

        return docs

    def getPitchSequences(self, pagen, meifile, zones):
        """Extract ngrams for note sequences from the MEI file"""
        notes = meifile.getElementsByName('note')
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

                location = self.getLocation(seq, meifile, zones)

                # get neumes
                neumes = self.getNeumes(seq, i)

                # get pitch names
                [pnames, midipitch] = self.getPitchNames(seq)

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
                intervals = self.getIntervals(semitones, pnames)

                # get contour - encode with Parsons code for musical contour
                contour = self.getContour(semitones)

                # save new document
                mydocs.append(
                        {
                            'id': str(uuid.uuid4()),
                            'type': self.TYPE,
                            'siglum_slug': self.siglum_slug,
                            'folio': pagen,
                            'pnames': pnames,
                            'neumes': neumes,
                            'contour': contour,
                            'semitones': str_semitones,
                            'intervals': intervals,
                            'location': str(location)
                        }
                )

        return mydocs

    def getShortNeumes(self, pagen, meifile, zones):
        """Extract single neumes whose note sequences are too short to be ngrams.

        Usually it is possible to do single neume search using the records
        created for note sequences. However, neumes whose note sequences are too
        short will only be indexed along with adjacent neumes. To be able to index
        them for single neume search we need to add them separately.
        """
        neume_docs = []

        for neume in meifile.getElementsByName('neume'):
            notes = neume.getDescendantsByName('note')

            if len(notes) < self.min_gram:
                location = self.getLocation(notes, meifile, zones)

                neume_docs.append({
                    'id': str(uuid.uuid4()),
                    'type': "cantusdata_music_notation",
                    'siglum_slug': self.siglum_slug,
                    'folio': pagen,
                    'neumes': str(neume.getAttribute('name').value),
                    'location': str(location)
                })

        return neume_docs