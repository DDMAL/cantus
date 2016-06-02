from django.core.management.base import BaseCommand
from optparse import make_option
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.concordance import Concordance
from cantusdata.models.manuscript import Manuscript
from cantusdata.signals.solr_sync import solr_synchronizer
from cantusdata.helpers.chant_importer import ChantImporter
import csv


class Command(BaseCommand):
    """
        Importing manuscripts will import from 'sources_export.csv'
        Importing concordances will import from 'concordances'
        It will import all manuscripts mentioned above
    """

    # List all possible types and their model
    TYPE_MAPPING = {'manuscripts': Manuscript, 'concordances': Concordance, 'chants': Chant}

    # All files must be in data-dumps/
    CHANT_FILE_MAPPING = {'salzinnes': 'salzinnes-chants.csv', 'st-gallen-390': 'st-gallen-390-chants.csv',
                          'st-gallen-391': 'st-gallen-391-chants.csv', 'utrecht-406': 'utrecht-406-chants.csv'}
    MANUSCRIPT_FILE = "sources-export.csv"
    CONCORDANCE_FILE = "concordances"

    help = 'Usage:'\
            '\tAdd everything you want to import as arguments. (or use --all)\n'\
            "\tSelect arguments from this list: {0}\n"\
            "\tTo import chants from a specific manuscript, add arguments from\n"\
            "\tthis list: {1},\n"\
            "\tor enter their full path from the data_dumps folder"\
            .format(TYPE_MAPPING.keys(), CHANT_FILE_MAPPING.keys())

    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Import all types: {0}'.format(TYPE_MAPPING.keys())),
    )

    # Used to specify which chant files to import
    chant_files = []

    def handle(self, *args, **options):
        if options['all']:
            args += tuple(self.TYPE_MAPPING.keys())

        # Go through the arguments to see if some files have been specified
        for arg in args:
            if arg in self.CHANT_FILE_MAPPING.keys():
                self.chant_files.append(self.CHANT_FILE_MAPPING[arg])
            elif arg.endswith('.csv'):
                self.chant_files.append(arg)

        # If no files were specified, import all of them
        if not self.chant_files:
            self.chant_files = self.CHANT_FILE_MAPPING.values()

        with solr_synchronizer.get_session():
            for type in self.TYPE_MAPPING.keys():
                if type in args:
                    # Remove the trailing 's' to make the type singular
                    type_singular = type.rstrip('s')

                    # Special case for chants, need to delete the folios too
                    if type == 'chants':
                        self.stdout.write('Deleting old folio data...')
                        Folio.objects.all().delete()

                    self.stdout.write('Deleting old {0} data...'.format(type_singular))
                    self.TYPE_MAPPING[type].objects.all().delete()

                    self.stdout.write('Importing new {0} data...'.format(type_singular))
                    # Call the method corresponding with the current type
                    getattr(self, 'import_{0}_data'.format(type_singular))(**options)

    def import_manuscript_data(self, **options):
        try:
            csv_file = csv.DictReader(open("data_dumps/{0}".format(self.MANUSCRIPT_FILE), "rU"))
        except IOError:
            raise IOError("File 'data_dumps/{0}' does not exist!".format(self.MANUSCRIPT_FILE))

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
        self.stdout.write("Successfully imported {0} manuscripts into database.".format(index))

    def import_concordance_data(self, **options):
        try:
            file = open("data_dumps/{0}".format(self.CONCORDANCE_FILE))
        except IOError:
            raise IOError("File 'data_dumps/{0}' does not exist!".format(self.CONCORDANCE_FILE))

        # Every line is a new concordance
        for index, line in enumerate(file.readlines()):
            # This method is pretty hacky, but it seems to work
            concordance = Concordance()

            concordance.letter_code = line.split(" ", 1)[0].strip()
            line = line.split(" ", 1)[1]

            concordance.institution_city = line.split(",", 1)[0].strip()
            line = line.split(",", 1)[1]

            concordance.institution_name = line.split(",", 1)[0].strip()
            line = line.split(",", 1)[1]

            concordance.library_manuscript_name = line.split(" (", 1)[0].strip()
            line = line.split(" (", 1)[1]

            concordance.date = line.split(", from", 1)[0].strip()
            line = line.split(", from", 1)[1]

            concordance.location = line.split(")", 1)[0].strip()
            line = line.split(")", 1)[1]

            line = line.split(": ", 1)[1]

            concordance.rism_code = line.split("]", 1)[0].strip()

            concordance.save()
        self.stdout.write("Successfully imported {0} concordances into database.".format(index))

    def import_chant_data(self, **options):
        for chant_file in self.chant_files:
            importer = ChantImporter(self.stdout)

            chant_count = importer.import_csv("data_dumps/{0}".format(chant_file))

            # Save the new chants
            importer.save()

            self.stdout.write("Successfully imported {0} chants into database.".format(chant_count))
