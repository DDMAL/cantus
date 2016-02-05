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

    systemcache = {}
    idcache = {}

    TYPE = "cantusdata_music_notation"


    ##### Constructor #####

    def __init__(self, folder_name, siglum_slug, min_gram=2, max_gram=10):
        self.folder_name = folder_name
        self.siglum_slug = siglum_slug

        self.min_gram = min_gram
        self.max_gram = max_gram

    #*****************************FUNCTIONS*******************************
    def findbyID(self, llist, mid, meifile):
        """ Returns the object in llist that has the given id. Used for finding
        zone. pymei function get_by_facs can be used instead, but this one is
        faster.
        """
        if mid in self.idcache:
            return self.idcache[mid]
        else:
            # idcache[mid] = llist[(i for i, obj in enumerate(llist) if obj.id == mid).next()]
            self.idcache[mid] = meifile.getElementById(mid)
            return self.idcache[mid]

    def getLocation(self, seq, meifile, zones, get_neume=lambda note: note):
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
        if seq[0].getId() not in self.systemcache:
            self.systemcache[seq[0].getId()] = meifile.lookBack(seq[0], "sb")
        if seq[endofsystem].getId() not in self.systemcache:
            self.systemcache[seq[endofsystem].getId()] = meifile.lookBack(
                    seq[endofsystem], "sb")

        if self.systemcache[seq[0].getId()] != self.systemcache[seq[
            endofsystem].getId()]:  #then the sequence spans two systems and we must store two seperate locations to highlight
            twosystems = 1
            for i in range(1, len(seq)):
                if seq[i - 1].getId() not in self.systemcache:
                    self.systemcache[seq[i - 1].getId()] = meifile.lookBack(
                            seq[i - 1], "sb")
                if seq[i] not in self.systemcache:
                    self.systemcache[seq[i].getId()] = meifile.lookBack(seq[i],
                                                                        "sb")

                # find the last note on the first system and the first note on the second system
                if self.systemcache[seq[i - 1].getId()] != self.systemcache[
                    seq[i].getId()]:
                    endofsystem = i  # this will be the index of the first note on second system

                    ulx1 = int(self.findbyID(zones,
                                             get_neume(seq[0]).getAttribute(
                                                     "facs").value,
                                             meifile).getAttribute("ulx").value)
                    lrx1 = int(self.findbyID(zones,
                                             get_neume(seq[i - 1]).getAttribute("facs").value,
                                             meifile).getAttribute("lrx").value)
                    ulx2 = int(self.findbyID(zones,
                                             get_neume(seq[i]).getAttribute(
                                                     "facs").value,
                                             meifile).getAttribute("ulx").value)
                    lrx2 = int(self.findbyID(zones,
                                             get_neume(seq[-1]).getAttribute(
                                                     "facs").value,
                                             meifile).getAttribute("lrx").value)
        else:  # the sequence is contained in one system and only one box needs to be highlighted
            ulx = int(self.findbyID(zones, get_neume(seq[0]).getAttribute("facs").value, meifile)
                      .getAttribute("ulx").value)
            lrx = int(self.findbyID(zones, get_neume(seq[-1]).getAttribute("facs").value, meifile)
                      .getAttribute("lrx").value)

        for note in seq:
            ulys.append(int(self.findbyID(zones, get_neume(note).getAttribute(
                                                  "facs").value,
                                          meifile).getAttribute("uly").value))
            lrys.append(int(self.findbyID(zones, get_neume(note).getAttribute(
                                                  "facs").value,
                                          meifile).getAttribute("lry").value))

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

        self.systemcache.clear()
        self.idcache.clear()

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
