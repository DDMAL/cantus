from django.core.management.base import BaseCommand
from cantusdata.models.manuscript import Manuscript
import csv
import sys

class Command(BaseCommand):
    args = ""
    debug = True

    def handle(self, *args, **kwargs):
        """
        Run "python manage.py import_manuscript_data filename.csv" to import
        a manuscript file into the db.  filename.csv must exist in /public/data_dumps/.
        """
        if args:
            csv_file_name = args[0]
        else:
            self.stdout.write("Please provide a file name!")
            sys.exit(-1)
        try:
            csv_file = csv.DictReader(open("data_dumps/" + str(csv_file_name), "rU"))
        except IOError:
            self.stdout.write(u"File {0} does not exist!".format(csv_file_name))
            sys.exit(-1)
        if self.debug:
            self.stdout.write("Deleting all old manuscript data...")
            # Nuke the db manuscripts
            Manuscript.objects.all().delete()
            self.stdout.write("Old manuscript data deleted.")
        # Load in the csv file.  This is a massive list of dictionaries.

        self.stdout.write("Starting manuscript import process.")
        # Create a manuscript and save it
        for index, row in enumerate(csv_file):
            manuscript = Manuscript()
            # TODO: Figure out what encodings to use...
            manuscript.name = unicode(row["Title"], "Latin-1")
            manuscript.siglum = unicode(row["Siglum"], "Latin-1")
            manuscript.date = unicode(row["Date"], "Latin-1")
            manuscript.provenance = unicode(row["Provenance"], "Latin-1")
            manuscript.description = unicode(row["Description"], "Latin-1")
            manuscript.save()
        self.stdout.write(u"Successfully imported {0} manuscripts into database.".format(index))
