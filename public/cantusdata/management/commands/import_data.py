from django.core.management.base import BaseCommand
from django.db import transaction
from optparse import make_option
from cantusdata.models.chant import Chant
from cantusdata.models.folio import Folio
from cantusdata.models.concordance import Concordance
from cantusdata.models.manuscript import Manuscript
from cantusdata.signals.solr_sync import solr_synchronizer
from cantusdata.helpers.chant_importer import ChantImporter
from cantusdata.helpers.scrapers.sources import sources
from cantusdata.helpers.scrapers.manuscript import parse as parse_manuscript
from cantusdata.helpers.scrapers.concordances import concordances
import csv
import re


class Command(BaseCommand):
    """
        Importing manuscripts will import from 'sources_export.csv'
        Importing concordances will import from 'concordances'
        It will import all manuscripts mentioned above
    """

    # List all possible types and their model
    TYPE_MAPPING = {'manuscripts': Manuscript, 'concordances': Concordance, 'chants': Chant}

    # All files must be in data-dumps/
    # The second item is the manuscript ID the chants are attached to
    CHANT_FILE_MAPPING = {
        'salzinnes': ['salzinnes-chants.csv', 133],
        'st-gallen-390': ['st-gallen-390-chants.csv', 127],
        'st-gallen-391': ['st-gallen-391-chants.csv', 128],
        'utrecht-406': ['utrecht-406-chants.csv', 51],
        'paris-12044': ['paris-12044.csv', 38]
    }
    MANUSCRIPT_FILE = "sources-export.csv"
    CONCORDANCE_FILE = "concordances"

    help = 'Usage: ./manage.py import_data {{{0}}} [chant_file [manuscript_id] ...]\n'\
            '\tAdd everything you want to import as arguments. (or use --all)\n'\
            "\tSelect arguments from this list: {1}\n"\
            "\tTo import chants from a specific manuscript, add arguments from\n"\
            "\tthis list: {2}\n" \
            "\tAlternatively, put a CSV file path as argument, followed by its manuscript ID"\
            .format('|'.join(list(TYPE_MAPPING.keys())), list(TYPE_MAPPING.keys()), list(CHANT_FILE_MAPPING.keys()))

    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Import all types: {0}'.format(list(TYPE_MAPPING.keys()))),
    )

    # Used to specify which chant files to import
    chants = []

    def handle(self, *args, **options):
        if options['all']:
            args += tuple(sorted(self.TYPE_MAPPING.keys()))

        # Go through the arguments to see if some files have been specified
        for index, arg in enumerate(args):
            if arg in list(self.CHANT_FILE_MAPPING.keys()):
                self.chants.append(self.CHANT_FILE_MAPPING[arg])
            elif arg not in list(self.TYPE_MAPPING.keys()) and arg.endswith('.csv') and index + 1 < len(args):
                self.chants.append([arg, args[index + 1]])

        # If no files were specified, import all of them
        if len(self.chants) == 0:
            self.chants = list(self.CHANT_FILE_MAPPING.values())

        with solr_synchronizer.get_session():
            for type in list(self.TYPE_MAPPING.keys()):
                if type in args:
                    # Remove the trailing 's' to make the type singular
                    type_singular = type.rstrip('s')

                    # Make an array of all the manuscript IDs
                    manuscript_ids = [ chant[1] for chant in self.chants ]

                    self.stdout.write('Deleting old {0} data...'.format(type_singular))
                    # Special case for chants, do not delete everything and we need to delete the folios
                    if type == 'chants':
                        Chant.objects.filter(manuscript__id__in=manuscript_ids).delete()
                        self.stdout.write('Deleting old folio data...')
                        Folio.objects.filter(manuscript__id__in=manuscript_ids).delete()
                    else:
                        self.TYPE_MAPPING[type].objects.all().delete()

                    self.stdout.write('Importing new {0} data...'.format(type_singular))
                    # Call the method corresponding with the current type
                    getattr(self, 'import_{0}_data'.format(type_singular))(**options)
            self.stdout.write("Waiting for Solr to finish...")

        self.stdout.write("Done.")

    @transaction.atomic
    def import_manuscript_data(self, **options):
        self.stdout.write("Starting manuscript import process.")
        i = 0
        for source, name in sources.items():
            self.stdout.write(source + ' ' + name)
            metadata = parse_manuscript(source, relative_url=True)
            manuscript = Manuscript()
            manuscript.name = metadata['Title']
            manuscript.cantus_url = metadata['CantusURL']
            manuscript.siglum = metadata["Siglum"] if 'Siglum' in metadata else ''
            manuscript.date = metadata["Date"] if 'Date' in metadata else ''
            manuscript.provenance = metadata["Provenance"] if 'Provenance' in metadata else ''
            manuscript.description = metadata["Summary"] if 'Summary' in metadata else ''
            manuscript.save()
            i += 1
        self.stdout.write("Successfully imported {0} manuscripts into database.".format(i))

    @transaction.atomic
    def import_concordance_data(self, **options):
        for idx, c in enumerate(concordances):
            concordance = Concordance()
            concordance.letter_code = c['letter_code']
            concordance.institution_city = c['institution_city']
            concordance.institution_name = c['institution_name']
            concordance.library_manuscript_name = c['library_manuscript_name']
            concordance.date = c['date']
            concordance.location = c['location']
            concordance.rism_code = c['rism_code']
            concordance.save()
        self.stdout.write("Successfully imported {0} concordances into database.".format(idx + 1))

    def import_chant_data(self, **options):
        for chant in self.chants:
            chant_file = chant[0]
            importer = ChantImporter(self.stdout)

            chant_count = importer.import_csv("data_dumps/{0}".format(chant_file))

            # Save the new chants
            importer.save()

            self.stdout.write("Successfully imported {0} chants into database.".format(chant_count))
