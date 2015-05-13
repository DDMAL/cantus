from StringIO import StringIO
import requests
from PIL import Image as PIL_Image
from lxml import etree
from neumeeditor.helpers.bounding_box import BoundingBox


def get_image(url):
    print "Fetching image: {0}".format(url)
    response = requests.get(url)
    return PIL_Image.open(StringIO(response.content))

def get_st_gallen_390_image_url(folio_name, ulx, uly, width, height):
    # The URL that we will serve from
    return "http://dev-diva.simssa.ca/fcgi-bin/iipsrv.fcgi?IIIF=/srv/images/cantus/ch-sgs-390/ch-sgs-{0}.jp2/{1},{2},{3},{4}/full/0/native.jpg".format(folio_name, ulx, uly, width, height)

def mei_element_name(xml_element_name):
    prefix = "{http://www.music-encoding.org/ns/mei}"
    return "{0}{1}".format(prefix, xml_element_name)


class MEI():
    root = None
    neumes = None
    # These are the containers for the data we will need
    surface = None
    layer = None

    def __init__(self, mei_file_string):
        # Build the XML tree
        self.root = etree.XML(mei_file_string)
        # Neumes are a dictionary
        self.neumes = {}
        # Get the containers
        name_space = "{http://www.music-encoding.org/ns/mei}"
        self.surface = self.root.find(mei_element_name("music")).find(mei_element_name("facsimile")).find(mei_element_name("surface"))
        self.layer = self.root.find(mei_element_name("music"))\
            .find(mei_element_name("body")).find(mei_element_name("mdiv"))\
            .find(mei_element_name("pages")).find(mei_element_name("page"))\
            .find(mei_element_name("system")).find(mei_element_name("staff"))\
            .find(mei_element_name("layer"))

    def build_neumes(self):
        # Flush the neume list
        self.neumes = {}
        # Get ulx, uly, lrx, lry from surface container
        # # Iterate through surface and get the zone info
        for zone in self.surface.iter():
            # Id has to have XML namespace
            id = zone.get("{http://www.w3.org/XML/1998/namespace}id")
            new_neume = BoundingBox()
            new_neume.ulx = zone.get("ulx")
            new_neume.uly = zone.get("uly")
            new_neume.lrx = zone.get("lrx")
            new_neume.lry = zone.get("lry")
            # Add to the big neume dictionary
            self.neumes.update({id: new_neume})
        # Now that we have the location, we need to extract the names from
        # another area of the MEI file
        # Iterate through layer and get the names
        for neume in self.layer.iter():
            # Get the id again
            id = neume.get("facs")
            try:
                # Retrieve the neume
                saved_neume = self.neumes[id]
                # print saved_neume
                # Save the name
                saved_neume.name = neume.get("name")
            except KeyError:
                # Name doesn't map onto a neume
                pass

    def get_neumes(self):
        return self.neumes.values()
