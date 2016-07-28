from django.core.management.base import BaseCommand
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from django.core.management import call_command
from optparse import make_option
import csv


class Command(BaseCommand):
    """
        Import a folio mapping (CSV file)
        Save that mapping to both django and Solr (through signals)

        Usage: See 'help' below
    """

    option_list = BaseCommand.option_list + (
        make_option('--no-refresh',
                    action='store_false',
                    dest='refresh',
                    default=True,
                    help='Do not refresh Solr after the import'),
    )

    help = 'Usage: ./manage.py import_folio_mapping <manuscript_id> <mapping_csv_file> [<manuscript2_id> <mapping_csv_file2> ...]'\
            '\n\tNote that csv files must be in the folder "data_dumps/folio_mapping/"'

    def handle(self, *args, **options):

        if len(args) == 0 or len(args) % 2 == 1:
            self.stdout.write(self.help)
            return

        manuscripts = []

        for index, arg in enumerate(args):
            if index % 2 == 0:
                temp_manuscript = {'id': arg}
            else:
                temp_manuscript['file'] = arg
                manuscripts.append(temp_manuscript)

        for manuscript in manuscripts:
            manuscript_id = manuscript['id']
            input_file = manuscript['file']

            try:
                manuscript = Manuscript.objects.get(id=manuscript_id)
            except IOError:
                raise IOError('Manuscript {0} does not exist'.format(manuscript_id))

            try:
                mapping_csv = csv.DictReader(open("data_dumps/folio_mapping/{0}".format(input_file), "rU"))
            except IOError:
                raise IOError("File data_dumps/folio_mapping/{0} does not exist".format(input_file))

            self.stdout.write("Starting import process for manuscript {0}".format(manuscript_id))

            for index, row in enumerate(mapping_csv):
                folio = row['folio']
                uri = row['uri']

                # Save in the Django DB
                try:
                    folio_obj = Folio.objects.get(number=folio, manuscript__id=manuscript_id)
                except Folio.DoesNotExist:
                    # If no folio is found, create one
                    folio_obj = Folio()
                    folio_obj.number = folio
                    folio_obj.manuscript = manuscript

                folio_obj.image_uri = uri
                folio_obj.save()

                if index > 0 and index % 50 == 0:
                    self.stdout.write("Imported {0} folios".format(index))

            self.stdout.write("All folios of manuscript {0} have been imported".format(manuscript_id))

        # Refreshing Solr chants is necessary since chants have a field image_uri
        # which is used when clicking on a search result
        if options['refresh']:
            self.stdout.write("Refreshing Solr chants after folio import")
            self.stdout.write()
            call_command('refresh_solr', 'chants', ' '.join([ str(man['id']) for man in manuscripts ]))
        else:
            self.stdout.write("Import process completed. To refresh Solr,"\
                                "use './manage.py refresh_solr chants [manuscript_id ...]'")
