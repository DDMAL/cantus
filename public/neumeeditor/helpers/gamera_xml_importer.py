from PIL import Image
from PIL import ImageDraw
from lxml import etree
from neumeeditor.models import Glyph
from neumeeditor.models.image import Image as NeumeEditorImage

def strip_neume_name(unstripped_name):
    lead = "neume."
    if unstripped_name.startswith(lead):
        return unstripped_name[len(lead):]
    else:
        return unstripped_name

def import_gamera_file(file_path):
    """
    Given a path, import the GameraXML file at that location.

    :param file_path:
    :return:
    """
    data_string = open(file_path).read()
    import_gamera_data(data_string)

def import_gamera_data(gamera_xml_string):
    # Build the file
    gamera = GameraXML(gamera_xml_string)
    # Get the names
    names = gamera.get_names()
    # Create glyphs
    for name in names:
        # If glyph doesn't exist, create it
        Glyph.objects.get_or_create(short_code=strip_neume_name(name))
    # Get the run length images
    rl_images = gamera.get_run_length_images()
    # for rl_image in rl_images:
    for name_and_image in rl_images:
        # Get the values
        name = strip_neume_name(name_and_image['name'])
        run_length_image = name_and_image['image']
        glyph, created = Glyph.objects.get_or_create(short_code=name)
        # Construct an image
        pil_image = run_length_image.get_image()
        image = NeumeEditorImage()
        image.set_PIL_image(pil_image)
        image.glyph = glyph
        image.set_md5()
        # Make sure not duplicate
        if not NeumeEditorImage.objects.filter(glyph=glyph, md5sum=image.md5sum):
            image.save()


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
            name = glyph.find("ids").find("id").get("name")
            run_length_data = glyph.find("data").text
            output.append(
                {
                    "name": name,
                    "image": RunLengthImage(width, height, run_length_data)
                }
            )
        return output


class RunLengthImage():
    width = None
    height = None
    run_length_data = None

    def __init__(self, width, height, run_length_data):
        self.width = width
        self.height = height
        # Turn run-length data into list of ints
        self.run_length_data = map(lambda x: int(x), run_length_data.split())

    def get_location_of_runlength(self, pixel_number):
        """
        Find the x,y location of the nth pixel of a run-length encoding.

        :param pixel_number: nth pixel, starting at 0 and ending at
         width * height - 1
        :return: (x,y) tuple
        """
        y = pixel_number / self.width
        x = pixel_number % self.width
        return x, y

    def get_image(self):
        image = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(image)
        current_pixel = 0
        is_black = False
        # Iterate through the run length data
        for length in self.run_length_data:
            for n in range(length):
                # 0 = white, 1 = black
                colour = 'white'
                if is_black:
                    colour = 'black'
                # Paint the pixel to the image
                draw.point(self.get_location_of_runlength(current_pixel), fill=colour)
                # Increase the current pixel
                current_pixel += 1
            # Switch from black to white or white to black
            is_black = not is_black
        # We're done drawing
        del draw
        return image