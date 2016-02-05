import uuid
import csv


# FIXME: This is used by the gall_hack mode of the import_mei command.
# What it's supposed to do is a mystery though, so it should probably be removed
# after verifying it isn't needed


class CSVParser():
    '''
    WORKAROUND CSV PARSER
    '''

    file_name = None
    siglum_slug = None

    # I don't know if this is really the right STEPREF.  I found it online...
    STEPREF = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    systemcache = {}
    idcache = {}


    def __init__(self, folder_name, siglum_slug):
        self.folder_name = folder_name
        self.siglum_slug = siglum_slug

    def parse(self):
        path = self.folder_name

        # TEMP
        shortest_gram = 2
        longest_gram = 10

        print self.folder_name

        # Load the csv file into a dict
        data = csv.DictReader(open(self.folder_name))

        data_lists = {}
        # The parser prefers a list format
        for row in data:
            folio = row['folio']
            if not data_lists.has_key(folio):
                # Add an list for the page
                data_lists[folio] = []
            # Append a new element to the list
            data_lists[folio].append({
                'ulx': row['ulx'],
                'uly': row['uly'],
                'neume': row['neume'],
                'lry': row['lry'],
                'lrx': row['lrx'],
                'id': row['id']
            })

        output = []
        for page in data_lists.keys():
            print data_lists[page]
            output.append(self.processMeiFile(folio, data_lists[page],
                                              shortest_gram, longest_gram))
        return output

    def convertStepToPs(self, step, oct):
        '''
        REMOVED FROM MUSIC21, so added here. -- AH

        Utility conversion; does not process internals.
        Takes in a note name string, octave number, and optional
        Accidental object.

        Returns a pitch space value as a floating point MIDI note number.

        >>> from music21 import *
        >>> pitch.convertStepToPs('c', 4, pitch.Accidental('sharp'))
        61.0
        >>> pitch.convertStepToPs('d', 2, pitch.Accidental(-2))
        36.0
        >>> pitch.convertStepToPs('b', 3, pitch.Accidental(3))
        62.0
        >>> pitch.convertStepToPs('c', 4, pitch.Accidental('half-flat'))
        59.5
        '''
        step = step.strip().upper()
        ps = float(((oct + 1) * 12) + self.STEPREF[step])
        return ps

    def findbyID(self, llist, mid, meifile):
        """ Returns the object in llist that has the given id. Used for finding zone.
            pymei function get_by_facs can be used instead, but this one is faster.
        """
        if mid in self.idcache:
            return self.idcache[mid]
        else:
            # idcache[mid] = llist[(i for i, obj in enumerate(llist) if obj.id == mid).next()]
            self.idcache[mid] = meifile.getElementById(mid)
            return self.idcache[mid]

    def getNeumes(self, seq, counter):
        """ Given a list of MEI note elements, return a string of the names of the neumes seperated by underscores.
        """
        neumes = str(seq[0]['neume'].lower().replace(" ", "_"))
        for k in range(1, counter):
            if seq[k]['id'] != seq[k - 1]['id']:
                neumes = neumes + '_' + str(
                    seq[k]['neume'].lower().replace(" ", "_"))
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
            # systemcache[seq[0]] = meifile.get_system(seq[0])
        if seq[endofsystem].getId() not in self.systemcache:
            self.systemcache[seq[endofsystem].getId()] = meifile.lookBack(
                seq[endofsystem], "sb")
            # systemcache[seq[endofsystem]] = meifile.get_system(seq[endofsystem])

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
                    # ulx1 = int(meifile.get_by_facs(seq[0].parent.parent.facs)[0].ulx)
                    # lrx1 = int(meifile.get_by_facs(seq[i-1].parent.parent.facs)[0].lrx)
                    # ulx2 = int(meifile.get_by_facs(seq[i].parent.parent.facs)[0].ulx)
                    # lrx2 = int(meifile.get_by_facs(seq[-1].parent.parent.facs)[0].lrx)
                    ulx1 = int(self.findbyID(zones,
                                             seq[0].parent.parent.getAttribute(
                                                 "facs").value,
                                             meifile).getAttribute("ulx").value)
                    lrx1 = int(self.findbyID(zones, seq[
                        i - 1].parent.parent.getAttribute("facs").value,
                                             meifile).getAttribute("lrx").value)
                    ulx2 = int(self.findbyID(zones,
                                             seq[i].parent.parent.getAttribute(
                                                 "facs").value,
                                             meifile).getAttribute("ulx").value)
                    lrx2 = int(self.findbyID(zones,
                                             seq[-1].parent.parent.getAttribute(
                                                 "facs").value,
                                             meifile).getAttribute("lrx").value)
        else:  # the sequence is contained in one system and only one box needs to be highlighted
            ulx = int(self.findbyID(zones, seq[0].parent.parent.getAttribute(
                "facs").value, meifile).getAttribute("ulx").value)
            lrx = int(self.findbyID(zones, seq[-1].parent.parent.getAttribute(
                "facs").value, meifile).getAttribute("lrx").value)
            # ulx = int(meifile.get_by_facs(seq[0].parent.parent.facs)[0].ulx)
            # lrx = int(meifile.get_by_facs(seq[-1].parent.parent.facs)[0].lrx)

        for note in seq:
            ulys.append(int(self.findbyID(zones,
                                          note.parent.parent.getAttribute(
                                              "facs").value,
                                          meifile).getAttribute("uly").value))
            lrys.append(int(self.findbyID(zones,
                                          note.parent.parent.getAttribute(
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

    def processMeiFile(self, folio, data_lists, shortest_gram, longest_gram):
        """
        Process the MEI file.

        :param data_lists:
        :param shortest_gram: int representing shortest gram length
        :param longest_gram: int representing longest gram length
        :return: list of dictionaries
        """
        # notes = data_lists['neume']
        # zones = meifile.getElementsByName('zone')
        nnotes = len(data_lists)

        mydocs = []

        for i in range(shortest_gram, longest_gram + 1):

            lrows = 0  #comment out this line if you want to process files that aren't already in the couch
            if lrows == 0:
                print "Processing pitch sequences... "
                # for j,note in enumerate(notes):
                for j in range(0, nnotes - i):
                    seq = data_lists[j:j + i]
                    # get box coordinates of sequence
                    # if ffile == "/Volumes/Copland/Users/ahankins/Documents/code/testing/Liber_Usualis_Final_Output/0012/0012_corr.mei":
                    #     pdb.set_trace()

                    # location = self.getLocation(seq, meifile, zones)
                    location_data = {
                        'ulx': [],
                        'uly': [],
                        'lrx': [],
                        'lry': []
                    }
                    for element in seq:
                        location_data['ulx'].append(int(element['ulx']))
                        location_data['uly'].append(int(element['uly']))
                        location_data['lrx'].append(int(element['lrx']))
                        location_data['lry'].append(int(element['lry']))
                    location = self.neume_box_border(location_data['ulx'],
                                                     location_data['uly'],
                                                     location_data['lrx'],
                                                     location_data['lry'])
                    #print 'location: ' + str(location)

                    # get neumes
                    neumes = self.getNeumes(seq, i)

                    # get pitch names
                    # [pnames, midipitch] = self.getPitchNames(seq)

                    # get semitones
                    # calculate difference between each adjacent entry in midipitch list
                    # semitones = [m-n for n, m in zip(midipitch[:-1], midipitch[1:])]
                    # str_semitones = str(semitones)[1:-1] # string will be stored instead of array for easy searching
                    # str_semitones = str_semitones.replace(', ', '_')

                    # intervals = self.getIntervals(semitones, pnames)

                    # get contour - encode with Parsons code for musical contour
                    # contour = self.getContour(semitones)
                    # save new document
                    mydocs.append(
                        {
                            'id': str(uuid.uuid4()),
                            'type': "cantusdata_music_notation",
                            'siglum_slug': self.siglum_slug,
                            'pagen': folio,
                            # 'project': int(project_id),
                            # 'pnames': pnames,
                            'neumes': neumes,
                            # 'contour': contour,
                            # 'semitones': str_semitones,
                            # 'intervals': intervals,
                            'location': str(location)
                        }
                    )
            else:
                print 'page {0} already processed\n'.format(folio)

        self.systemcache.clear()
        self.idcache.clear()

        return mydocs

    def neume_box_border(self, ulx_list, uly_list, lrx_list, lry_list):
        ulx = min(ulx_list)
        uly = min(uly_list)
        lrx = max(lrx_list)
        lry = max(lry_list)
        width = lrx - ulx
        height = lry - uly
        return [{'width': width, 'ulx': ulx, 'uly': uly, 'height': height}]