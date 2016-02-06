from abc import ABCMeta, abstractmethod

import os
import pymei


class AbstractMEIConverter:
    """
    This class extracts a record for each location (bounding box) on the page that we might want to
    highlight in our web application. We consider all pitch sequences 2--10 notes long. If a pitch
    sequence spans two systems, two separate bounding boxes are stored in the same record.

    Throughout this script, ulx and uly stand for upper left x and y coordinates respectively and lrx and
    lry stand for lower right coordinates.
    """

    __metaclass__ = ABCMeta

    folder_name = None
    siglum_slug = None

    TYPE = "cantusdata_music_notation"


    ##### Constructor #####

    def __init__(self, folder_name, siglum_slug, min_gram=2, max_gram=10):
        self.folder_name = folder_name
        self.siglum_slug = siglum_slug

        self.min_gram = min_gram
        self.max_gram = max_gram

    #*****************************FUNCTIONS*******************************
    def getLocation(self, seq, cache, get_neume=lambda note: note):
        """ Given a sequence of notes and the corresponding MEI Document, calculates
        and returns the json formatted list of  locations (box coordinates) to be
        stored for an instance of a pitch sequence in our CouchDB.  If the sequence
        is contained in a single system, only one location will be stored. If the
        sequence spans two systems, a list of two locations will be stored.
        """
        ulys = []
        lrys = []
        twosystems = 0
        endofsystem = len(seq) - 1

        if cache.getSystemId(seq[0]) != cache.getSystemId(seq[endofsystem]):
            # Then the sequence spans two systems and we must store two separate locations to highlight
            twosystems = 1
            for i in range(1, len(seq)):
                # find the last note on the first system and the first note on the second system
                if cache.getSystemId(seq[i - 1]) != cache.getSystemId(seq[i]):
                    endofsystem = i  # this will be the index of the first note on second system

                    ulx1 = int(cache.getNeumeZone(get_neume(seq[0])).getAttribute("ulx").value)
                    lrx1 = int(cache.getNeumeZone(get_neume(seq[i - 1])).getAttribute("lrx").value)
                    ulx2 = int(cache.getNeumeZone(get_neume(seq[i])).getAttribute("ulx").value)
                    lrx2 = int(cache.getNeumeZone(get_neume(seq[-1])).getAttribute("lrx").value)
        else:
            # The sequence is contained in one system and only one box needs to be highlighted
            ulx = int(cache.getNeumeZone(get_neume(seq[0])).getAttribute("ulx").value)
            lrx = int(cache.getNeumeZone(get_neume(seq[-1])).getAttribute("lrx").value)

        for note in seq:
            zone = cache.getNeumeZone(get_neume(note))

            ulys.append(int(zone.getAttribute("uly").value))
            lrys.append(int(zone.getAttribute("lry").value))

        if twosystems:
            uly1 = min(ulys[:endofsystem])
            uly2 = min(ulys[endofsystem:])
            lry1 = max(lrys[:endofsystem])
            lry2 = max(lrys[endofsystem:])
            return [
                {"ulx": int(ulx1), "uly": int(uly1), "height": abs(uly1 - lry1),
                 "width": abs(ulx1 - lrx1)},
                {"ulx": int(ulx2), "uly": int(uly2), "height": abs(uly2 - lry2),
                 "width": abs(ulx2 - lrx2)}]
        else:
            uly = min(ulys)
            lry = max(lrys)
            return [{"ulx": int(ulx), "uly": int(uly), "height": abs(uly - lry),
                     "width": abs(ulx - lrx)}]

    def processMeiFile(self, ffile):
        """
        Process the MEI file.

        :param ffile:
        :return: list of dictionaries
        """
        print '\nProcessing ' + str(ffile) + '...'

        mei_doc = pymei.documentFromFile(str(ffile), False).getMeiDocument()
        page_number = getPageNumber(ffile)

        docs = self.getNgramDocuments(mei_doc, page_number)

        return docs

    @abstractmethod
    def getNgramDocuments(self, mei_doc, page_number):
        raise NotImplementedError('getNgramDocuments()')

    #***************************** MEI PROCESSING ****************************

    def parse(self):

        path = self.folder_name

        # Generate list of files to process, preferring human-corrected MEI files
        meifiles = []
        for bd, dn, fn in os.walk(path):
            if ".git" in bd:
                continue
            for f in fn:
                if f.startswith("."):
                    continue
                if ".mei" in f:
                    meifiles.append(os.path.join(bd, f))
                    print "Adding {0}".format(f)

        meifiles.sort()

        # Iterate through each MEI file in directory
        # This list will represent one manuscript
        output = []
        for ffile in meifiles:
            output.append(self.processMeiFile(ffile))
        return output


class LookupCache:
    """Utility for quick lookup of systems and zones"""
    def __init__(self, doc):
        self._doc = doc
        self._zones = {zone.getId(): zone for zone in doc.getElementsByName('zone')}
        self._system_cache = {}

    def getNeumeZone(self, neume):
        return self._zones[neume.getAttribute('facs').value]

    def getSystemId(self, elem):
        elem_id = elem.getId()

        try:
            return self._system_cache[elem_id]
        except KeyError:
            system = elem.lookBack('sb')
            system_id = system.getId() if system else None

            self._system_cache[elem_id] = system_id
            return system_id



def getPageNumber(ffile):
    """
    Extract the page number from the file name

    :param ffile:
    :return: page number as a string
    """
    return str(ffile).split('_')[-1].split('.')[0]


def getNeumeNames(neumes):
    """Get the neume names in a string separated by underscores

    :param neumes: A list of MEI neume elements
    """
    return '_'.join(str(neume.getAttribute('name').value) for neume in neumes)
