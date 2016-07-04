from itertools import groupby


def getLocation(tokens):
    """Get bounding boxes with the locations of the notes

    Given a sequence of notes and the corresponding MEI Document, calculates
    and returns the json formatted list of  locations (box coordinates) to be
    stored for an instance of a pitch sequence in our CouchDB.  If the sequence
    is contained in a single system, only one location will be stored. If the
    sequence spans two systems, a list of two locations will be stored.
    """
    locs = []

    for group in getTokensBySystem(tokens):
        ulx = min(tok.location['ulx'] for tok in group)
        uly = min(tok.location['uly'] for tok in group)
        lrx = max(tok.location['lrx'] for tok in group)
        lry = max(tok.location['lry'] for tok in group)

        locs.append({
            'ulx': ulx,
            'uly': uly,
            'height': lry - uly,
            'width': lrx - ulx
        })

    return locs


def getTokensBySystem(tokens):
    for (_, group) in groupby(tokens, lambda tok: tok.system):
        yield list(group)
