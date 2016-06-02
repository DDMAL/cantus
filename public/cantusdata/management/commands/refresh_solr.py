from django.core.management.base import BaseCommand
from optparse import make_option
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript
from cantusdata import settings
import solr


TYPES = ('manuscripts', 'chants')
MODELS = {'manuscript': Manuscript, 'chant': Chant}


class Command(BaseCommand):
    help = 'Usage:'\
           '\tAdd everything you want to refresh as arguments.\n'\
           '\tSelect arguments from this list: {0}'.format(TYPES)

    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Refresh all types: {0}'.format(TYPES)),
    )

    def handle(self, *args, **options):
        solr_conn = solr.SolrConnection(settings.SOLR_SERVER)
        solr_records = []

        if options['all']:
            args += TYPES

        for type in TYPES:
            if type in args:
                # Remove the trailing 's' to make the type singular
                type = type.rstrip('s')

                self.stdout.write('Flushing {0} data...'.format(type))
                solr_conn.delete_query('type:cantusdata_{0}'.format(type))
                self.stdout.write('Creating Solr {0} records...'.format(type))

                model = MODELS[type]
                for object in model.objects.all():
                    solr_records.append(object.create_solr_record())

        self.stdout.write('Re-adding data... (may take a few minutes)')
        solr_conn.add_many(solr_records)
        self.stdout.write('Committing changes...')
        solr_conn.commit()
