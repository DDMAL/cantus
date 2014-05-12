import xmlDict
from PIL import Image
import sys

glyph_list = xmlDict.ConvertXmlToDict('page_glyphs.xml')['gamera-database']['glyphs']['glyph']
imageIn = Image.open('img.tif')
imageOut = imageIn
for curGlyph in glyph_list:
	redPixel = (255,0,0)
	startX = int(curGlyph['ulx'])
	startY = int(curGlyph['uly'])

	width = int(curGlyph['ncols'])
	height = int(curGlyph['nrows'])

	for xPix in range(startX, startX+width):
		imageOut.putpixel((xPix, startY), redPixel)

	for xPix in range(startX, startX+width):
		imageOut.putpixel((xPix, startY + height), redPixel)

	for yPix in range(startY, startY+height):
		imageOut.putpixel((startX, yPix), redPixel)

	for yPix in range(startY, startY+height):
		imageOut.putpixel((startX + width, yPix), redPixel)

imageOut.save('img2.tif')