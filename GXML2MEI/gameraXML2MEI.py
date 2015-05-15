import os, os.path
import itertools
import csv
import logging
import argparse

from uuid import uuid4
from lxml import etree

from pymei import MeiDocument, MeiElement, MeiAttribute, XmlExport


class GameraXMLConverter:
    def __init__(self, xmlFile, meiFile, neumeNames):
        self.xmlFile = xmlFile
        self.meiFile = meiFile
        self.neumeNames = neumeNames

        self.conversionInfo = {}

        self._initMEI()

    def processGamera(self, dumpVisualization=False):
        zones, neumes = self.getMEIContent(dumpVisualization=dumpVisualization)

        for element in zones:
            self.surface.addChild(element)

        for element in neumes:
            self.initLayer.addChild(element)

    def write(self):
        XmlExport.meiDocumentToFile(self.meiDoc, self.meiFile)

    def getMEIContent(self, dumpVisualization=False):
        """Extract zones and neumes from the source file"""

        neumeElements = []
        zones = []

        for elem in etree.parse(self.xmlFile).xpath('/gamera-database/glyphs/glyph'):
            # Get the relevant attributes from the glyph element
            startX = int(elem.get('ulx'))
            endX = startX + int(elem.get('ncols'))

            startY = int(elem.get('uly'))
            endY = startY + int(elem.get('nrows'))

            curNeumeName = elem.xpath('string(./ids/id/@name)')

            # Create the MEI neume element
            newNeumeElement = MeiElement('neume')
            neumeElements.append(newNeumeElement)

            newNeumeElement.id = generate_MEI_ID()

            splitName = curNeumeName[curNeumeName.find(".") + 1:]
            if(splitName in self.neumeNames):
                newNeumeElement.addAttribute(MeiAttribute('name', self.neumeNames[splitName]))
            elif len(splitName) < 3:
                newNeumeElement.addAttribute(MeiAttribute('name', "Letter " + splitName.upper()))
            else:
                newNeumeElement.addAttribute(MeiAttribute('name', splitName))

            zoneID = generate_MEI_ID()
            newNeumeElement.addAttribute(MeiAttribute('facs', zoneID))
            zones.append(Zone(zoneID, startX, startY, endX, endY))

        zoneElements = []

        for zone in self._sortZones(zones, dumpVisualization=dumpVisualization):
            newZoneElement = MeiElement('zone')
            zoneElements.append(newZoneElement)

            newZoneElement.id = zone.id
            newZoneElement.addAttribute(MeiAttribute('ulx', str(zone.startX)))
            newZoneElement.addAttribute(MeiAttribute('uly', str(zone.startY)))
            newZoneElement.addAttribute(MeiAttribute('lrx', str(zone.endX)))
            newZoneElement.addAttribute(MeiAttribute('lry', str(zone.endY)))

        return zoneElements, neumeElements

    def _initMEI(self):
        """Initialize a new MEI document

        Sets the attributes meiDoc, surface, and initLayer
        """

        self.meiDoc = MeiDocument()

        root = MeiElement("mei")
        root.id = generate_MEI_ID()
        self.meiDoc.root = root

        #needs meiHead here
        meiHead = MeiElement('meiHead')
        fileDesc = MeiElement('fileDesc')
        titleStmt = MeiElement('titleStmt')
        title = MeiElement('title')
        pubStmt = MeiElement('pubStmt')
        date = MeiElement('date')
        encodingDesc = MeiElement('encodingDesc')
        projectDesc = MeiElement('projectDesc')
        p = MeiElement('p')

        music = MeiElement('music')
        facsimile = MeiElement('facsimile')

        self.surface = MeiElement('surface')

        # Label the surface with the name of the input file, which could help
        # identify the original image
        label = os.path.basename(os.path.splitext(self.xmlFile)[0])
        self.surface.addAttribute(MeiAttribute('label', label))

        #systems get added to page
        #neumes get added to systems

        body = MeiElement('body')
        mdiv = MeiElement('mdiv')
        pages = MeiElement('pages')
        page = MeiElement('page')
        page.id = generate_MEI_ID()

        initSystem = MeiElement('system')
        initSystem.id = generate_MEI_ID()

        initStaff = MeiElement('staff')
        initStaff.id = generate_MEI_ID()

        self.initLayer = MeiElement('layer')
        self.initLayer.id = generate_MEI_ID()

        root.addChild(meiHead)
        meiHead.addChild(fileDesc)
        fileDesc.addChild(titleStmt)
        titleStmt.addChild(title)
        fileDesc.addChild(pubStmt)
        pubStmt.addChild(date)
        meiHead.addChild(encodingDesc)
        encodingDesc.addChild(projectDesc)
        projectDesc.addChild(p)

        root.addChild(music)
        music.addChild(facsimile)
        facsimile.addChild(self.surface)
        music.addChild(body)
        body.addChild(mdiv)
        mdiv.addChild(pages)
        pages.addChild(page)
        page.addChild(initSystem)
        initSystem.addChild(initStaff)
        initStaff.addChild(self.initLayer)

    def _sortZones(self, zones, dumpVisualization=False):
        # Sort zones by their center point
        zones.sort(key=lambda a: a.centerY)

        # Get the total distance between the center points of every adjacent pair of zones
        totalCenterGaps = 0

        for i in xrange(len(zones) - 2, -1, -2):
            totalCenterGaps += zones[i + 1].centerY - zones[i].centerY

        averageGap = float(totalCenterGaps) / (len(zones) - 1)
        logging.debug('average gap is %s', averageGap)

        clusters = []

        # Build initial clusters of overlapping zones
        for zone in reversed(zones):
            if not clusters:
                clusters.append(ZoneCluster([zone]))
                continue

            # Iterate through all existing clusters to find an one which overlaps
            # the zone, to within a tolerance of the average gap
            for cluster in reversed(clusters):
                if overlaps(zone, cluster, averageGap):
                    cluster.addZone(zone)
                    break

            # If no existing cluster overlapped, initialize a new cluster
            else:
                clusters.append(ZoneCluster([zone]))

        logging.debug('initially found %s clusters. consolidating...', len(clusters))
        self.conversionInfo['initialClusters'] = len(clusters)

        if dumpVisualization:
            initialClusters = dict()
            for i in range(len(clusters)):
                initialClusters.update((zone, i+1) for zone in clusters[i].zones)

        # Consolidate overlapping clusters
        for i in xrange(len(clusters) - 1):
            clusterA = clusters[i]

            # If we've removed this cluster, skip it
            if not clusterA:
                continue

            for j in xrange(i + 1, len(clusters)):
                clusterB = clusters[j]

                # If we haven't already removed cluster B and it overlaps cluster A,
                # copy its zones into cluster A and then remove it
                # FIXME: should this use averageGap as a tolerance threshold?
                if clusterB and overlaps(clusterA, clusterB):
                    clusterA.extendWithZones(clusterB)
                    clusters[j] = None

        # Sort clusters by their upper y value and sort the zones in each cluster
        # by their upper left points
        clusters = sorted((cluster for cluster in clusters if cluster), key=lambda c: c.startY)

        logging.info('found %s zones which form %s clusters', len(zones), len(clusters))
        self.conversionInfo['zones'] = len(zones)
        self.conversionInfo['clusters'] = len(clusters)

        for cluster in clusters:
            cluster.zones = cluster.sortedZones()

        if dumpVisualization:
            # Dump an SVG representation of the zones and clusters to file
            self.dumpZoneVisualization(clusters, averageGap, initialClusters)

        return itertools.chain(*(cluster.zones for cluster in clusters))

    def generateOverlaidImage(self, inputTiff, outputTiff):
        """Output a TIFF with the zone bounding box overlaid over the neumes

        Requires PIL to be installed
        """
        from PIL import Image

        imageIn = Image.open(inputTiff)
        imageOut = imageIn

        for curGlyph in etree.parse(self.xmlFile).xpath('/gamera-database/glyphs/glyph'):
            redPixel = (255,0,0)
            startX = int(curGlyph.get('ulx'))
            startY = int(curGlyph.get('uly'))

            width = int(curGlyph.get('ncols'))
            height = int(curGlyph.get('nrows'))

            for xPix in xrange(startX, startX+width):
                imageOut.putpixel((xPix, startY), redPixel)

            for xPix in xrange(startX, startX+width):
                imageOut.putpixel((xPix, startY + height), redPixel)

            for yPix in xrange(startY, startY+height):
                imageOut.putpixel((startX, yPix), redPixel)

            for yPix in xrange(startY, startY+height):
                imageOut.putpixel((startX + width, yPix), redPixel)

        imageOut.save(outputTiff)

    def dumpZoneVisualization(self, clusters, averageGap, initialClusters):
        """Output an (ugly) SVG file showing the relation between zones and clusters
        """

        outPath, filename = os.path.split(self.meiFile)
        dumpFile = os.path.join(outPath, os.path.splitext(filename)[0] + '_clusters.svg')

        height = max(cluster.endY for cluster in clusters)
        width = max(max(zone.endX for zone in cluster.zones) for cluster in clusters)

        with open(dumpFile, 'w') as f:
            f.write('''\
<?xml version="1.0" standalone="yes"?>
<svg viewBox="0 0 {width} {height}" version="1.1"
     xmlns="http://www.w3.org/2000/svg">'''.format(height=height, width=width))

            f.write('<!-- Clusters -->\n')

            clusterIndex = 1
            for cluster in clusters:
                f.write('  <rect x="0" y="{startY}" height="{yDelta}" width="{width}" '
                        'stroke-width="5" stroke="blue" fill="gainsboro" title="Cluster {idx}"/>\n'
                        .format(startY=cluster.startY, yDelta=cluster.endY - cluster.startY, width=width, idx=clusterIndex))

                clusterIndex += 1

            f.write('<!-- Zones -->\n')

            clusterIndex = zoneIndex = 1
            for cluster in clusters:
                for zone in cluster.zones:
                    # Draw the actual zone
                    zoneHeight = zone.endY-zone.startY
                    zoneWidth = zone.endX-zone.startX

                    f.write('  <rect x="{startX}" y="{startY}" width="{width}" '
                            'height="{height}" stroke-width="3" stroke="black" '
                            'fill="yellow" title="Zone {idx}, initial cluster {initialCluster}, ID {id}"/>\n'
                            .format(idx=zoneIndex, initialCluster=initialClusters[zone], id=zone.id, startX=zone.startX, startY=zone.startY,
                                    width=zoneWidth, height=zoneHeight))

                    # Draw the midpoint and bars representing the average gap
                    centerX = zone.startX + (zone.endX - zone.startX) / 2
                    centerY = zone.centerY

                    # Find a tolerable radius for the midpoint
                    radius = max(min(zoneHeight, zoneWidth) / 5, 3)

                    f.write('  <circle cx="{centerX}" cy="{centerY}" r="{radius}" fill="black" />\n'
                            .format(centerX=centerX, centerY=centerY, radius=radius))

                    f.write('  <path d="M {centerX}, {startY} v -{averageGap} '
                            'h {barLen} h -{barLenTimes2}" stroke-width="3" '
                            'stroke="black" fill="none" />\n'
                            .format(centerX=centerX, startY=zone.startY, averageGap=averageGap, barLen=zoneWidth/2, barLenTimes2=zoneWidth))
                    f.write('  <path d="M {centerX}, {endY} v {averageGap} '
                            'h {barLen} h -{barLenTimes2}" stroke-width="3" '
                            'stroke="black" fill="none" />\n'
                            .format(centerX=centerX, endY=zone.endY, averageGap=averageGap, barLen=zoneWidth/2, barLenTimes2=zoneWidth))

                    zoneIndex += 1

                clusterIndex += 1

            f.write('\n</svg>')


class Zone:
    def __init__(self, zoneId, startX, startY, endX, endY):
        self.id = zoneId

        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY

        self.centerY = float(startY - endY) / 2 + endY


class ZoneCluster:
    def __init__(self, zones):
        self.zones = zones
        self.startY = min(zone.startY for zone in zones)
        self.endY = max(zone.endY for zone in zones)

    def addZone(self, zone):
        self.zones.append(zone)
        self.startY = min(self.startY, zone.startY)
        self.endY = max(self.endY, zone.endY)

    def extendWithZones(self, otherCluster):
        self.zones.extend(otherCluster.zones)
        self.startY = min(self.startY, otherCluster.startY)
        self.endY = max(self.endY, otherCluster.endY)

    def sortedZones(self):
        return sorted(self.zones, key=lambda z: z.startX)


def overlaps(regionA, regionB, tolerance=0):
    """overlaps(a, b[, tolerance]) => return true if two horizontal regions overlap

    Allows a variable tolerance threshold.
    """

    # Check cases where one of the endpoints of region A are contained
    # within region B
    for point in (regionA.startY, regionA.endY):
        if isWithin(point, regionB.startY - tolerance, regionB.endY + tolerance):
            return True

    # If neither of regions A's endpoints fall within region B, then
    # the only way they could overlap is if region B is entirely contained
    # within region A. Test one of region B's endpoints to look for that case.
    # (Really any point in region B would do, so don't worry about the tolerance.)
    return isWithin(regionB.startY, regionA.startY, regionA.endY)


def isWithin(point, start, end):
    """
    Return true if point falls within start and end
    """
    return point >= start and point <= end


def generate_MEI_ID():
    return 'm-' + str(uuid4())


def loadNeumeNames(csvFile):
    """Load neume names from a CSV file"""
    with open(csvFile, mode='rU') as infile:
        reader = csv.reader(infile)
        return {rows[1]: rows[0] for rows in reader}


def main(args):
    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.INFO)

    neumeNames = loadNeumeNames('ccnames.csv')

    fileList = [f for f in os.listdir(args.input_directory)
                if os.path.isfile(os.path.join(args.input_directory, f)) and f.endswith('.xml')]

    if not fileList:
        logging.warn('Did not find any files in %s', args.input_directory)
        return

    logging.debug('Found files: %s', fileList)

    for relativeFile in fileList:
        logging.info('processing file %s', relativeFile)

        inFile = os.path.join(args.input_directory, relativeFile)
        outFile = os.path.join(args.output_directory, os.path.splitext(relativeFile)[0] + '.mei')

        converter = GameraXMLConverter(inFile, outFile, neumeNames)

        if args.dump_zone_overlay:
            converter.generateOverlaidImage(args.dump_zone_overlay[0], args.dump_zone_overlay[1])

        converter.processGamera(dumpVisualization=args.dump_zone_clusters)

        converter.write()


def initializeArgumentParser(parser):
    parser.add_argument('input_directory', nargs='?', help='directory with the input (defaults to working directory)',
                        default='.')

    parser.add_argument('output_directory', nargs='?', help='directory for the output (defaults to working directory)',
                        default='.')

    parser.add_argument('-v', '--verbose', action='store_true', help='increase the verbosity')

    parser.add_argument('--dump-zone-clusters', action='store_true',
                        help='write a visualization of the zone clusters to file')

    parser.add_argument('--dump-zone-overlay', nargs=2, metavar='TIFF',
                        help='create a copy of the TIFF image with the zones overlaid')

    return parser


if __name__ == '__main__':
    main(args=initializeArgumentParser(argparse.ArgumentParser()).parse_args())