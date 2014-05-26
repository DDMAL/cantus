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
        a manuscript file into the db.
        filename.csv must exist in /public/data_dumps/.
        """
        if args:
            csv_file_name = args[0]
        else:
            self.stdout.write("Please provide a file name!")
            sys.exit(-1)
        try:
            csv_file = csv.DictReader(open("data_dumps/" + str(csv_file_name),
                                           "rU"))
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
            manuscript.name = row["Title"].decode("utf-8").strip()
            manuscript.siglum = row["Siglum"].decode("utf-8").strip()
            manuscript.date = row["Date"].decode("utf-8").strip()
            manuscript.provenance = row["Provenance"].decode("utf-8").strip()
            manuscript.description = row["Description"].decode("utf-8").strip()
            manuscript.save()
        self.stdout.write(
            u"Successfully imported {0} manuscripts into database."
            .format(index))
