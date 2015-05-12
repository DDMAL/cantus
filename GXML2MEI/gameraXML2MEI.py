import os
import itertools
import csv
import logging

from uuid import uuid4
import xmlDict

from pymei import MeiDocument, MeiElement, MeiAttribute, XmlExport

#todo: have zone point to neume rather than vice versa


def processGamera(xmlFile, neumeNames):
    """Extract zones and neumes from xmlFile
    :param xmlFile: path to the Gamera XML file
    :param neumeNames: a dict mapping to full neume names
    """
    glyphList = xmlDict.ConvertXmlToDict(xmlFile)['gamera-database']['glyphs']['glyph']
    #except indexerror for "not a gameraXML file"

    logging.info('processing file %s', xmlFile)

    neumeElements = []
    zones = []

    for curGlyph in glyphList:
        startX = int(curGlyph['ulx'])
        endX = int(curGlyph['ulx']) + int(curGlyph['ncols'])

        startY = int(curGlyph['uly'])
        endY = int(curGlyph['uly']) + int(curGlyph['nrows'])

        newNeumeElement = MeiElement('neume')
        neumeElements.append(newNeumeElement)

        newNeumeElement.id = generate_MEI_ID()
        curNeumeName = curGlyph['ids']['id']['name']
        splitName = curNeumeName[curNeumeName.find(".") + 1:]
        if(splitName in neumeNames):
            newNeumeElement.addAttribute(MeiAttribute('name', neumeNames[splitName]))
        elif len(splitName) < 3:
            newNeumeElement.addAttribute(MeiAttribute('name', "Letter " + splitName.upper()))
        else:
            newNeumeElement.addAttribute(MeiAttribute('name', splitName))

        zoneID = generate_MEI_ID()
        newNeumeElement.addAttribute(MeiAttribute('facs', zoneID))
        zones.append(Zone(zoneID, startX, startY, endX, endY))

    # Allow garbage collection of the original Gamera glyphs
    glyphList = None

    zoneElements = []

    for zone in sortZones(zones, xmlFile, dumpVisualization=False):
        newZoneElement = MeiElement('zone')
        zoneElements.append(newZoneElement)

        newZoneElement.id = zone.id
        newZoneElement.addAttribute(MeiAttribute('ulx', str(zone.startX)))
        newZoneElement.addAttribute(MeiAttribute('uly', str(zone.startY)))
        newZoneElement.addAttribute(MeiAttribute('lrx', str(zone.endX)))
        newZoneElement.addAttribute(MeiAttribute('lry', str(zone.endY)))

    return zoneElements, neumeElements


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


def sortZones(zones, xmlFile, dumpVisualization=False):
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
        for clusterIndex in xrange(len(clusters) - 1, -1, -1):
            cluster = clusters[clusterIndex]

            if overlaps(zone, cluster, averageGap):
                cluster.addZone(zone)
                break

        # If no existing cluster overlapped, initialize a new cluster
        else:
            clusters.append(ZoneCluster([zone]))

    logging.debug('initially found %s clusters. consolidating...', len(clusters))

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
            # FIXME: should this use averageGap as a threshold?
            if clusterB and overlaps(clusterA, clusterB):
                clusterA.extendWithZones(clusterB)
                clusters[j] = None

    # Sort clusters by their upper y value and sort the zones in each cluster
    # by their upper left points
    clusters = sorted((cluster for cluster in clusters if cluster), key=lambda c: c.startY)

    logging.info('found %s zones which form %s clusters', len(zones), len(clusters))

    for cluster in clusters:
        cluster.zones = cluster.sortedZones()

    if dumpVisualization:
        # Dump an SVG representation of the zones and clusters to file
        _dumpZoneVisualization(xmlFile, clusters, averageGap, initialClusters)

    return itertools.chain(*(cluster.zones for cluster in clusters))


def overlaps(regionA, regionB, threshold=0):
    """overlaps(a, b[, threshold]) => return true if two horizontal regions overlap

    Allows a tolerance of threshold.
    """

    # Check cases where one of the endpoints of region A are contained
    # within region B
    for point in (regionA.startY, regionA.endY):
        if isWithin(point, regionB.startY - threshold, regionB.endY + threshold):
            return True

    # If neither of regions A's endpoints fall within region B, then
    # the only way they could overlap is if region B is entirely contained
    # within region A. Test one of region B's endpoints to look for that case.
    # (Really any point in region B would do, so don't worry about the threshold.)
    return isWithin(regionB.startY, regionA.startY, regionA.endY)


def isWithin(point, start, end):
    """
    Return true if point falls within start and end
    """
    return point >= start and point <= end


def init_MEI_document():
    """Create a new MEI document. Return a tuple (meiDocument, surface, initialLayer).
    """

    meiDocOut = MeiDocument()

    root = MeiElement("mei")
    root.id = generate_MEI_ID()
    meiDocOut.root = root

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
    surface = MeiElement('surface')

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
    initLayer = MeiElement('layer')
    initLayer.id = generate_MEI_ID()

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
    facsimile.addChild(surface)
    music.addChild(body)
    body.addChild(mdiv)
    mdiv.addChild(pages)
    pages.addChild(page)
    page.addChild(initSystem)
    initSystem.addChild(initStaff)
    initStaff.addChild(initLayer)

    return meiDocOut, surface, initLayer


def generate_MEI_ID():
    return 'm-' + str(uuid4())


def _dumpZoneVisualization(xmlFile, clusters, averageGap, initialClusters):
    '''Output an (ugly) SVG file showing the relation between zones and clusters
    '''

    filename = 'dump_'+xmlFile+'.svg'

    height = max(cluster.endY for cluster in clusters)
    width = max(max(zone.endX for zone in cluster.zones) for cluster in clusters)

    with open(filename, 'w') as f:
        f.write('''\
<?xml version="1.0" standalone="yes"?>
<svg viewBox="0 0 {width} {height}" version="1.1"
     xmlns="http://www.w3.org/2000/svg">
'''.format(height=height, width=width))

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


def main():
    # usage = "%prog [options] input_directory output_directory data_output_directory"
    # parser = OptionParser(usage)
    # options, args = parser.parse_args()
    #
    # if len(args) < 1:
    #     print("You must specify an input directory.")
    #     sys.exit(-1)

    logging.getLogger().setLevel(logging.INFO)

    with open('ccnames.csv', mode='rU') as infile:
        reader = csv.reader(infile)
        neumeNames = {rows[1]:rows[0] for rows in reader}

    fileList = [f for f in os.listdir('.') if (os.path.isfile(f) and f.endswith('.xml'))]
    logging.info('Found files: %s', fileList)

    for xmlFile in fileList:
        meiDocOut, surface, initLayer = init_MEI_document()

        zones, neumes = processGamera(xmlFile, neumeNames)

        for element in zones:
            surface.addChild(element)

        for element in neumes:
            initLayer.addChild(element)

        fileName = xmlFile[:-4]
        XmlExport.meiDocumentToFile(meiDocOut, fileName+'.mei')


if __name__ == '__main__':
    main()