from itertools import groupby


def getLocation(notes, cache, get_neume=lambda note: note):
    """Get bounding boxes with the locations of the notes

    Given a sequence of notes and the corresponding MEI Document, calculates
    and returns the json formatted list of  locations (box coordinates) to be
    stored for an instance of a pitch sequence in our CouchDB.  If the sequence
    is contained in a single system, only one location will be stored. If the
    sequence spans two systems, a list of two locations will be stored.
    """
    locs = []

    for (_, group) in groupby(notes, cache.getSystemId):
        zones = [cache.getNeumeZone(get_neume(note)) for note in group]

        ulx = min(getCoordFromZones(zones, 'ulx'))
        uly = min(getCoordFromZones(zones, 'uly'))
        lrx = max(getCoordFromZones(zones, 'lrx'))
        lry = max(getCoordFromZones(zones, 'lry'))

        locs.append({
            'ulx': ulx,
            'uly': uly,
            'height': lry - uly,
            'width': lrx - ulx
        })

    return locs


def getCoordFromZones(zones, c):
    return [int(zone.getAttribute(c).value) for zone in zones]


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
