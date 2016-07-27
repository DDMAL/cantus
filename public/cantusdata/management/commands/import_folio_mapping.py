from django.core.management.base import BaseCommand
from cantusdata.models.folio import Folio
from cantusdata.models.manuscript import Manuscript
from django.core.management import call_command
import csv


class Command(BaseCommand):
    """
        Import a folio mapping (CSV file)
        Save that mapping to both django and Solr (through signals)

        Usage: See 'help' below
    """

    help = 'Usage: ./manage.py import_folio_mapping <manuscript_id> [mapping_csv_file]'\
            '\n\tNote that the csv file must be in the folder "data_dumps/folio_mapping/"'\
            '\n\tIf no csv file is provided, <manuscript_id>.csv will be used instead'

    def handle(self, *args, **kwargs):

        if len(args) == 0:
            self.stdout.write(self.help)
            return

        manuscript_id = args[0]
        try:
            manuscript = Manuscript.objects.get(id=manuscript_id)
        except IOError:
            raise IOError('Manuscript {0} does not exist'.format(manuscript_id))

        if len(args) > 1:
            input_file = args[1]
        else:
            input_file = "{0}.csv".format(manuscript_id)

        try:
            mapping_csv = csv.DictReader(open("data_dumps/folio_mapping/{0}".format(input_file), "rU"))
        except IOError:
            raise IOError("File data_dumps/folio_mapping/{0} does not exist".format(args[1]))

        self.stdout.write("Starting import process")

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

        self.stdout.write("All folios have been imported")

        # Refreshing Solr chants is necessary since chants have a field image_uri
        # which is used when clicking on a search result
        self.stdout.write("Refreshing Solr chants")
        call_command('refresh_solr', 'chants')
