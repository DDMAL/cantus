import os
import pymei
from django.test import TestCase
from cantusdata.helpers.mei_conversion.abstract_mei_converter import AbstractMEIConverter, LookupCache


RESOURCE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../../test_data'))


class StubbedConverter (AbstractMEIConverter):
    def getNgramDocuments(self, mei_doc, page_number):
        return []


class GetLocationTestCase (TestCase):
    def testSingleSystemLocation(self):
        doc = getDocument('390_024.mei')
        seq = doc.getElementsByName('neume')[:3]

        loc = self.getLocation(doc, seq)

        self.assertListEqual(loc, [getCoords(seq)])

    def testLocationWithSystemBreak(self):
        doc = getDocument('salz_001r.mei')

        sb = doc.getElementsByName('sb')[1]

        peers = list(sb.getPeers())
        i = peers.index(sb)

        # FIXME: Make this less fragile
        firstSeq = list(peers[i - 2].getDescendantsByName('note'))
        secondSeq = list(peers[i + 2].getDescendantsByName('note'))
        seq = firstSeq + secondSeq

        loc = self.getLocation(doc, seq, get_neume=getNoteWithinNeume)
        expected = [getCoords(firstSeq, getNoteWithinNeume), getCoords(secondSeq, getNoteWithinNeume)]

        self.assertListEqual(loc, expected)

    def getLocation(self, doc, seq, get_neume=lambda note: note):
        return StubbedConverter('dummy', 'dummy').getLocation(seq, LookupCache(doc), get_neume=get_neume)


def getDocument(resource):
    infile = os.path.join(RESOURCE_PATH, resource)
    return pymei.documentFromFile(str(infile), False).getMeiDocument()


def getNoteAsNeume(note):
    return note


def getNoteWithinNeume(note):
    return note.parent.parent


def getCoords(notes, getNeume=getNoteAsNeume):
    zones = [getZoneFor(getNeume(neume)) for neume in notes]

    ulx = min(getCoord(zones, 'ulx'))
    uly = min(getCoord(zones, 'uly'))
    lrx = max(getCoord(zones, 'lrx'))
    lry = max(getCoord(zones, 'lry'))

    return {
        'ulx': ulx,
        'uly': uly,
        'width': lrx - ulx,
        'height': lry - uly
    }


def getZoneFor(neume):
    doc = neume.document
    fac = neume.getAttribute('facs').value

    return doc.getElementById(fac)


def getCoord(zones, c):
    return [int(zone.getAttribute(c).value) for zone in zones]
