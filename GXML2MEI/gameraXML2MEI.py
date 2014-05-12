import xmlDict
import sys
from pymei import MeiDocument, MeiElement, MeiAttribute, XmlExport
import random

glyph_list = xmlDict.ConvertXmlToDict('page_glyphs.xml')['gamera-database']['glyphs']['glyph']

def generate_MEI_ID():
	return '%030x' % random.randrange(16**30)

#meiDict = {}
#meiDict['mei'] = {'meiHead': {}, 'music': {}}
#meiDict['mei']['meiHead'] = {'fileDesc': {'titleStmt': {'title': ''}, 'pubStmt': '',}}
#meiDict['mei']['music'] = {'facsimile': {}, 'body':{}}

meiDocOut = MeiDocument()

root = MeiElement("mei")
root.id = generate_MEI_ID()
meiDocOut.root = root

zones = []

for curGlyph in glyph_list:
	startX = curGlyph['ulx']
	endX = str(int(curGlyph['ulx']) + int(curGlyph['ncols']))

	startY = curGlyph['uly']
	endY = str(int(curGlyph['uly']) + int(curGlyph['nrows']))

	zones.append(MeiElement('zone'))
	zoneIndex = len(zones) - 1

	zones[zoneIndex].id = generate_MEI_ID()
	zones[zoneIndex].addAttribute(MeiAttribute('ulx', startX))
	zones[zoneIndex].addAttribute(MeiAttribute('uly', startY))
	zones[zoneIndex].addAttribute(MeiAttribute('lrx', endX))
	zones[zoneIndex].addAttribute(MeiAttribute('lry', endY))

for element in zones:
	root.addChild(element)

XmlExport.meiDocumentToFile(meiDocOut, 'testdoc.mei')