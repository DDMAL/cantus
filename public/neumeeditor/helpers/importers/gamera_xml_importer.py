from neumeeditor.helpers.gamera_xml import GameraXML
from neumeeditor.helpers.importers.abstract_importer import AbstractImporter
from neumeeditor.helpers.string import strip_leading_characters
from neumeeditor.models.glyph import get_or_create_glyph
from neumeeditor.models.image import Image as NeumeEditorImage


class GameraXMLImporter(AbstractImporter):

    def import_data(self):
        # Build the file
        gamera = GameraXML(self.file_string)
        # Get the names
        names = gamera.get_names()
        # Create glyphs
        # self.create_glyphs(names)
        # Get the run length images
        rl_images = gamera.get_run_length_images()
        # for rl_image in rl_images:
        for name_and_image in rl_images:
            # Get the values
            name = strip_leading_characters(name_and_image['name'], "neume.")
            run_length_image = name_and_image['image']
            glyph, created = get_or_create_glyph(name)
            # Create the image
            self.create_image(run_length_image, glyph)

    def create_glyphs(self, names):
        '''
        Given a list of names, create glyphs (if they don't already exist).

        :param names: A list of name strings.
        :return: void
        '''
        for name in names:
            # If glyph doesn't exist, create it
            get_or_create_glyph(strip_leading_characters(name, "neume."))

    def create_image(self, run_length_image, glyph):
        '''
        Create an Image model for a particular RunLengthImage.

        :param run_length_image: A RunLengthImage object.
        :param glyph:
        :return: void
        '''
        pil_image = run_length_image.get_image()
        image = NeumeEditorImage()
        image.set_PIL_image(pil_image)
        image.glyph = glyph
        image.ulx = run_length_image.ulx
        image.uly = run_length_image.uly
        image.width = run_length_image.width
        image.height = run_length_image.height
        image.folio_name = self.file_name
        image.set_md5()
        # Make sure not duplicate
        if not NeumeEditorImage.objects.filter(glyph=glyph, md5sum=image.md5sum):
            image.save()


def import_gamera_file(file_path):
    """
    Given a path, import the GameraXML file at that location.

    :param file_path:
    :return:
    """
    file = open(file_path)
    data_string = file.read()
    file_name = file.name
    importer = GameraXMLImporter(data_string, file_name)
    importer.import_data()
