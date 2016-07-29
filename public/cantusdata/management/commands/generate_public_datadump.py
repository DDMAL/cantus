from django.core.management.base import BaseCommand
from cantusdata.models.manuscript import Manuscript
import csv


class Command(BaseCommand):

    CSV_PATH = 'data_dumps/public-manuscripts.csv'

    help = 'Usage: ./manage.py generate_public_datadump\n' \
           '\tGenerates the file \'{0}\' based on the Django DB data.'.format(CSV_PATH)

    def handle(self, *args, **options):
        try:
            writer = csv.writer(open(self.CSV_PATH, "w"))
        except IOError:
            raise IOError("File '{0}' does not exist!".format(self.CSV_PATH))

        self.stdout.write("Starting process.")

        data = [['id', 'cantus_url', 'manifest_url', 'plugins']]

        for manuscript in Manuscript.objects.filter(public=True):
            plugins = ','.join([plugin.name for plugin in manuscript.plugins.all() ])
            row = [manuscript.id, manuscript.cantus_url, manuscript.manifest_url, plugins]
            data.append(row)

        writer.writerows(data)

        self.stdout.write("Successfully generated new public manuscript data dump file.")