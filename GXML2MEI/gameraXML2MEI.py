import xmlDict
import sys, os
import csv
from pymei import MeiDocument, MeiElement, MeiAttribute, XmlExport
import random
from uuid import uuid4
from optparse import OptionParser

#todo: have zone point to neume rather than vice versa


def processGamera(xmlFile, neumeNames):
    """Extract zones and neumes from xmlFile
    :param xmlFile: path to the Gamera XML file
    :param neumeNames: a dict mapping to full neume names
    """
    glyphList = xmlDict.ConvertXmlToDict(xmlFile)['gamera-database']['glyphs']['glyph']
    #except indexerror for "not a gameraXML file"

    zoneElements = []
    neumeElements = []

    for curGlyph in glyphList:
        startX = curGlyph['ulx']
        endX = str(int(curGlyph['ulx']) + int(curGlyph['ncols']))

        startY = curGlyph['uly']
        endY = str(int(curGlyph['uly']) + int(curGlyph['nrows']))

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

        newZoneElement = MeiElement('zone')
        zoneElements.append(newZoneElement)

        newZoneElement.id = generate_MEI_ID()
        #newZoneElement.addAttribute(MeiAttribute('neume', neumes[neumeIndex].id))
        newZoneElement.addAttribute(MeiAttribute('ulx', startX))
        newZoneElement.addAttribute(MeiAttribute('uly', startY))
        newZoneElement.addAttribute(MeiAttribute('lrx', endX))
        newZoneElement.addAttribute(MeiAttribute('lry', endY))

        newNeumeElement.addAttribute(MeiAttribute('facs', newZoneElement.id))

    return zoneElements, neumeElements


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


def main():
    # usage = "%prog [options] input_directory output_directory data_output_directory"
    # parser = OptionParser(usage)
    # options, args = parser.parse_args()
    #
    # if len(args) < 1:
    #     print("You must specify an input directory.")
    #     sys.exit(-1)

    neumeNames = {}
    with open('ccnames.csv', mode='rU') as infile:
        reader = csv.reader(infile)
        neumeNames = {rows[1]:rows[0] for rows in reader}

    print neumeNames

    fileList = [f for f in os.listdir('.') if (os.path.isfile(f) and f.endswith('.xml'))]
    print fileList
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