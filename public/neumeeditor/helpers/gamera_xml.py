from lxml import etree
from neumeeditor.helpers.run_length_image import RunLengthImage


class GameraXML():
    root = None
    symbols = None
    glyphs = None

    def __init__(self, gamera_file_string):
        self.root = etree.fromstring(gamera_file_string)
        self.symbols = self.root[0]
        self.glyphs = self.root[1]

    def get_names(self):
        output = []
        for symbol in self.symbols:
            output.append(symbol.get("name"))
        return output

    def get_run_length_images(self):
        """
        Get the run_length images and their names.

        :return: List of {name:name, image:image} dicts.
        """
        output = []
        for glyph in self.glyphs:
            width = int(glyph.get("ncols"))
            height = int(glyph.get("nrows"))
            ulx = int(glyph.get("ulx"))
            uly = int(glyph.get("uly"))
            print ulx, uly
            name = glyph.find("ids").find("id").get("name")
            run_length_data = glyph.find("data").text
            output.append(
                {
                    "name": name,
                    "image": RunLengthImage(ulx, uly, width, height,
                                            run_length_data)
                }
            )
        return output
