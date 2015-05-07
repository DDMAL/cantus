import csv
from django.core.management.base import BaseCommand
from cantusdata.settings import BASE_DIR
from neumeeditor.helpers.gamera_xml_importer import import_gamera_file


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        # Re-save every image, thereby regenerating all thumbnails
        #for i in range(15, 191):
        for i in range(15, 20):
            file_name = "390_{0}".format(str(i).zfill(3))
            import_gamera_file(BASE_DIR + "/data_dumps/gamera_xml/{0}".format(file_name))
            print "GameraXML file {0} imported.".format(file_name)
