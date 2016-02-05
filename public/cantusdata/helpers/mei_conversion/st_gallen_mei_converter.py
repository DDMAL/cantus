import uuid
import string
import pymei

from .abstract_mei_converter import AbstractMEIConverter


class StGallenMEIConverter (AbstractMEIConverter):
    """
    An MEI convereter which works with the St Gallen MEI format
    """

    def getNeumes(self, seq, counter):
        """ Given a list of MEI note elements, return a string of the names of
        the neumes seperated by underscores.
        """
        neumes = str(seq[0].getAttribute('name').value)
        for k in range(1, counter):
            if seq[k].id != seq[k - 1].id:
                neumes = neumes + '_' + str(seq[k].getAttribute('name').value)
        return neumes

    def getLocation(self, seq, meifile, zones):
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

        if self.systemcache[seq[0].getId()] != self.systemcache[
            seq[endofsystem].getId()]:
            #then the sequence spans two systems and we must store two seperate locations to highlight
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
                    ulx1 = int(
                            self.findbyID(zones, seq[0].getAttribute("facs").value,
                                          meifile).getAttribute("ulx").value)
                    lrx1 = int(self.findbyID(zones, seq[i - 1].getAttribute(
                            "facs").value, meifile).getAttribute("lrx").value)
                    ulx2 = int(
                            self.findbyID(zones, seq[i].getAttribute("facs").value,
                                          meifile).getAttribute("ulx").value)
                    lrx2 = int(
                            self.findbyID(zones, seq[-1].getAttribute("facs").value,
                                          meifile).getAttribute("lrx").value)
        else:  # the sequence is contained in one system and only one box needs to be highlighted
            ulx = int(self.findbyID(zones, seq[0].getAttribute("facs").value,
                                    meifile).getAttribute("ulx").value)
            lrx = int(self.findbyID(zones, seq[-1].getAttribute("facs").value,
                                    meifile).getAttribute("lrx").value)

        for note in seq:
            ulys.append(int(
                    self.findbyID(zones, note.getAttribute("facs").value,
                                  meifile).getAttribute("uly").value))
            lrys.append(int(
                    self.findbyID(zones, note.getAttribute("facs").value,
                                  meifile).getAttribute("lry").value))

        if twosystems:
            uly1 = min(ulys[:endofsystem])
            uly2 = min(ulys[endofsystem:])
            lry1 = max(lrys[:endofsystem])
            lry2 = max(lrys[endofsystem:])
            return [{
                "ulx": int(ulx1),
                "uly": int(uly1),
                "height": abs(uly1 - lry1),
                "width": abs(ulx1 - lrx1)
            },
                {
                    "ulx": int(ulx2),
                    "uly": int(uly2),
                    "height": abs(uly2 - lry2),
                    "width": abs(ulx2 - lrx2)
                }]
        else:
            uly = min(ulys)
            lry = max(lrys)
            return [{
                "ulx": int(ulx),
                "uly": int(uly),
                "height": abs(uly - lry),
                "width": abs(ulx - lrx)
            }]

    def processMeiFile(self, ffile):
        """
        Process the MEI file.

        :param ffile:
        :return: list of dictionaries
        """
        print '\nProcessing ' + str(ffile) + '...'

        meifile = pymei.documentFromFile(str(ffile), False).getMeiDocument()

        print "ffile:"
        print ffile

        page = meifile.getElementsByName('page')
        pagen = self.getPageNumber(ffile)

        neumes = meifile.getElementsByName('neume')

        zones = meifile.getElementsByName('zone')
        n_neumes = len(neumes)  # number of notes in file
        print("n_neumes: {0}, shortest_gram: {1}, longest_gram: {2}".format(
                n_neumes, self.min_gram, self.max_gram))

        mydocs = []

        for i in range(self.min_gram, self.max_gram + 1):
            print "Processing pitch sequences..."
            for j in range(0, n_neumes - i):
                seq = neumes[j:j + i]
                location = self.getLocation(seq, meifile, zones)

                # get neumes
                n_gram_neumes = self.getNeumes(seq, i).lower()
                n_gram_neumes_no_punctuation = n_gram_neumes.replace(
                        '_', ' ').translate(string.maketrans("", ""),
                                            string.punctuation).replace(' ',
                                                                        '_')

                new_doc = {
                    'id': str(uuid.uuid4()),
                    'type': self.TYPE,
                    'siglum_slug': self.siglum_slug,
                    'folio': pagen,
                    'neumes': n_gram_neumes_no_punctuation,
                    'location': str(location)
                }

                mydocs.append(new_doc)

        self.systemcache.clear()
        self.idcache.clear()

        return mydocs
