def getLocation(seq, cache, get_neume=lambda note: note):
    """Get bounding boxes with the locations of the notes

    Given a sequence of notes and the corresponding MEI Document, calculates
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
