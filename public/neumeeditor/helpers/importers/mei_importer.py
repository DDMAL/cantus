from neumeeditor.helpers.importers.abstract_importer import AbstractImporter
from neumeeditor.helpers.mei import MEI, get_image, get_st_gallen_390_image_url
from neumeeditor.models import Name
from neumeeditor.models.glyph import get_or_create_glyph
from neumeeditor.models.image import Image


class MeiImporter(AbstractImporter):
    def import_data(self):
        # Build the file
        mei = MEI(self.file_string)
        mei.build_neumes()
        neumes = mei.get_neumes()
        # Create the glyphs
        for neume in neumes:
            if neume.name is None:
                print "NONE ERROR"
                continue
            # Check if the name already exists
            name, name_created = Name.objects.get_or_create(string=neume.name)
            glyph, glyph_created = get_or_create_glyph(neume.name)
            # Assign the new glyph to the name and save the name
            name.glyph = glyph
            name.save()
            # Create the image
            self.create_image(glyph, neume)

    def create_image(self, glyph, neume):
        '''
        Create an image for the particular neume.

        :param glyph:
        :param neume:
        :return:
        '''
        pil_image = get_image(
            get_st_gallen_390_image_url(self.file_name, neume.ulx, neume.uly,
                                        neume.get_width(), neume.get_height()))
        # Create Image model
        image = Image()
        image.glyph = glyph
        image.set_PIL_image(pil_image)
        image.set_md5()
        image.ulx = neume.ulx
        image.uly = neume.uly
        image.folio_name = self.file_name
        image.width = neume.get_width()
        image.height = neume.get_height()
        # Make sure not duplicate
        if not Image.objects.filter(glyph=glyph, md5sum=image.md5sum):
            image.save()


def import_mei_file(file_path):
    file = open(file_path)
    data_string = open(file_path).read()
    importer = MeiImporter(data_string, file.name)
    importer.import_data()
