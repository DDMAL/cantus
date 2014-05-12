import xmlDict
import sys
from pymei import MeiDocument, MeiElement, MeiAttribute, XmlExport
import random
from uuid import uuid4

glyph_list = xmlDict.ConvertXmlToDict('page_glyphs.xml')['gamera-database']['glyphs']['glyph']

def generate_MEI_ID():
	return 'm-' + str(uuid4())

#meiDict = {}
#meiDict['mei'] = {'meiHead': {}, 'music': {}}
#meiDict['mei']['meiHead'] = {'fileDesc': {'titleStmt': {'title': ''}, 'pubStmt': '',}}
#meiDict['mei']['music'] = {'facsimile': {}, 'body':{}}

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

	zones.append(MeiElement('zone'))
	zoneIndex = len(zones) - 1

	zones[zoneIndex].id = generate_MEI_ID()
	zones[zoneIndex].addAttribute(MeiAttribute('ulx', startX))
	zones[zoneIndex].addAttribute(MeiAttribute('uly', startY))
	zones[zoneIndex].addAttribute(MeiAttribute('lrx', endX))
	zones[zoneIndex].addAttribute(MeiAttribute('lry', endY))

	neumes.append(MeiElement('neume'))
	neumeIndex = len(neumes) - 1

	neumes[neumeIndex].id = generate_MEI_ID()
	neumes[neumeIndex].addAttribute(MeiAttribute('facs', zones[zoneIndex].id))
	neumes[neumeIndex].addAttribute(MeiAttribute('name', curGlyph['ids']['id']['name']))


music = MeiElement('music')
facsimile = MeiElement('facsimile')
surface = MeiElement('surface')

layout = MeiElement('layout') #gets added to music
page = MeiElement('page') #gets added to layout
#systems get added to page

body = MeiElement('body')

root.addChild(music)
music.addChild(facsimile)
music.addChild(body)
facsimile.addChild(surface)

for element in zones:
	surface.addChild(element)

for element in neumes:
	body.addChild(element)

XmlExport.meiDocumentToFile(meiDocOut, 'testdoc.mei')