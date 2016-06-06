from django.core.management.base import BaseCommand
from optparse import make_option
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.folio import Folio
from cantusdata import settings
import solr


class Command(BaseCommand):

    TYPE_MAPPING = {'manuscripts': Manuscript, 'chants': Chant, 'folios': Folio}

    help = 'Usage:'\
           '\tAdd everything you want to refresh as arguments.\n'\
           '\tSelect arguments from this list: {0}'.format(TYPE_MAPPING.keys())

    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Refresh all types: {0}'.format(TYPE_MAPPING.keys())),
    )

    def handle(self, *args, **options):
        solr_conn = solr.SolrConnection(settings.SOLR_SERVER)
        solr_records = []

        if options['all']:
            args += tuple(self.TYPE_MAPPING.keys())

        for type in self.TYPE_MAPPING.keys():
            if type in args:
                # Remove the trailing 's' to make the type singular
                type_singular = type.rstrip('s')

                self.stdout.write('Flushing {0} data...'.format(type_singular))
                solr_conn.delete_query('type:cantusdata_{0}'.format(type_singular))
                self.stdout.write('Creating Solr {0} records...'.format(type_singular))

                model = self.TYPE_MAPPING[type]
                for object in model.objects.all():
                    solr_records.append(object.create_solr_record())

        self.stdout.write('Re-adding data... (may take a few minutes)')
        solr_conn.add_many(solr_records)
        self.stdout.write('Committing changes...')
        solr_conn.commit()
