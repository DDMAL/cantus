import xmlDict
import sys, os
from pymei import MeiDocument, MeiElement, MeiAttribute, XmlExport
import random
from uuid import uuid4
from optparse import OptionParser

#todo: have zone point to neume rather than vice versa


def generate_MEI_ID():
	return 'm-' + str(uuid4())

'''usage = "%prog [options] input_directory output_directory data_output_directory"
parser = OptionParser(usage)
options, args = parser.parse_args()

if len(args) < 1:
    print("You must specify an input directory.")
    sys.exit(-1)'''

fileList = [f for f in os.listdir('.') if (os.path.isfile(f) and f.endswith('.xml'))]

for xmlFile in fileList:
	fileName = xmlFile[:-4]
	glyph_list = xmlDict.ConvertXmlToDict(xmlFile)['gamera-database']['glyphs']['glyph']
	#except indexerror for "not a gameraXML file"
	meiDocOut = MeiDocument()

	root = MeiElement("mei")
	root.id = generate_MEI_ID()
	meiDocOut.root = root

	zones = []
	neumes = []

	for curGlyph in glyph_list:
		startX = curGlyph['ulx']
		endX = str(int(curGlyph['ulx']) + int(curGlyph['ncols']))

		startY = curGlyph['uly']
		endY = str(int(curGlyph['uly']) + int(curGlyph['nrows']))

		neumes.append(MeiElement('neume'))
		neumeIndex = len(neumes) - 1

		neumes[neumeIndex].id = generate_MEI_ID()
		neumes[neumeIndex].addAttribute(MeiAttribute('name', curGlyph['ids']['id']['name']))

		zones.append(MeiElement('zone'))
		zoneIndex = len(zones) - 1

		zones[zoneIndex].id = generate_MEI_ID()
		zones[zoneIndex].addAttribute(MeiAttribute('neume', neumes[neumeIndex].id))
		zones[zoneIndex].addAttribute(MeiAttribute('ulx', startX))
		zones[zoneIndex].addAttribute(MeiAttribute('uly', startY))
		zones[zoneIndex].addAttribute(MeiAttribute('lrx', endX))
		zones[zoneIndex].addAttribute(MeiAttribute('lry', endY))


	#needs meiHead here
	music = MeiElement('music')
	facsimile = MeiElement('facsimile')
	surface = MeiElement('surface')

	layout = MeiElement('layout') #gets added to music
	page = MeiElement('page') #gets added to layout
	#systems get added to page
	#neumes get added to systems

	body = MeiElement('body')

	root.addChild(music)
	music.addChild(facsimile)
	music.addChild(body)
	facsimile.addChild(surface)

	for element in zones:
		surface.addChild(element)

	for element in neumes:
		body.addChild(element)

	XmlExport.meiDocumentToFile(meiDocOut, fileName+'.mei')