import requests
from StringIO import StringIO
from PIL import Image as PIL_Image
from lxml import etree
from neumeeditor.models import Glyph, Name
from neumeeditor.models.fields.short_code_field import sanitize_short_code
from neumeeditor.models.image import Image


def get_image(url):
    print "Fetching image: {0}".format(url)
    response = requests.get(url)
    return PIL_Image.open(StringIO(response.content))

def get_st_gallen_390_image_url(folio_name, ulx, uly, width, height):
    # The URL that we will serve from
    return "http://dev-diva.simssa.ca/fcgi-bin/iipsrv.fcgi?IIIF=/srv/images/cantus/ch-sgs-390/ch-sgs-{0}.jp2/{1},{2},{3},{4}/full/0/native.jpg".format(folio_name, ulx, uly, width, height)

def import_mei_file(file_path):
    data_string = open(file_path).read()
    import_mei_data(data_string)

def import_mei_data(mei_string, file_name):
    # Build the file
    mei = MEI(mei_string)
    mei.build_neumes()
    neumes = mei.get_neumes()
    # Create the glyphs
    for neume in neumes:
        if neume.name is None:
            print "NONE ERROR"
            continue
        # Check if the name already exists
        name, name_created = Name.objects.get_or_create(string=neume.name)
        glyph, glyph_created = Glyph.objects.get_or_create(short_code=sanitize_short_code(neume.name))
        # Assign the new glyph to the name and save the name
        name.glyph = glyph
        name.save()
        # Create the image
        pil_image = get_image(get_st_gallen_390_image_url(file_name, neume.ulx, neume.uly, neume.get_width(), neume.get_height()))
        # Create Image model
        image = Image()
        image.glyph = glyph
        image.set_PIL_image(pil_image)
        image.set_md5()
        image.save()

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
            new_neume = Neume()
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


class Neume():
    ulx = None
    uly = None
    lrx = None
    lry = None
    name = None

    def __unicode__(self):
        return u"neume[name: {0}, ulx: {1}, uly: {2}, lrx: {3}, lry: {4}]".format(self.name, self.ulx, self.uly, self.lrx, self.lry)

    def get_width(self):
        return int(self.lrx) - int(self.ulx)

    def get_height(self):
        return int(self.lry) - int(self.uly)
