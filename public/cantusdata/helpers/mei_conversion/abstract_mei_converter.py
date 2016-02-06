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
