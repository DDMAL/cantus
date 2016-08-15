from django.core.management.base import BaseCommand
from optparse import make_option
from cantusdata.models.chant import Chant
from cantusdata.models.manuscript import Manuscript
from cantusdata.models.folio import Folio
from cantusdata import settings
import solr


class Command(BaseCommand):

    TYPE_MAPPING = {'manuscripts': Manuscript, 'chants': Chant, 'folios': Folio}

    help = 'Usage: ./manage.py refresh_solr {{{0}}} [manuscript_id ...]'\
           '\n\tSpecify manuscript ID(s) to only refresh selected items in that/those manuscript(s)'\
           '\n\tUse --all to refresh all {1} types.'.format('|'.join(TYPE_MAPPING.keys()), len(TYPE_MAPPING))

    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Refresh all types: {0}'.format(TYPE_MAPPING.keys())),
    )

    def handle(self, *args, **options):
        solr_conn = solr.SolrConnection(settings.SOLR_SERVER)

        types = []
        manuscript_ids = None

        if options['all']:
            types += self.TYPE_MAPPING.keys()
        elif len(args) == 0:
            self.stdout.write(self.help)
            return
        elif len(args) > 0:
            types.append(args[0])

        if len(args) > 1:
            manuscript_ids = args[1:]

        for type in types:
            # Remove the trailing 's' to make the type singular
            type_singular = type.rstrip('s')
            model = self.TYPE_MAPPING[type]

            self.stdout.write('Flushing {0} data...'.format(type_singular))

            if manuscript_ids:
                formatted_ids = '(' + ' OR '.join(manuscript_ids) + ')'
                if model == Manuscript:
                    delete_query = 'type:cantusdata_{0} AND item_id:{1}'.format(type_singular, formatted_ids)
                else:
                    delete_query = 'type:cantusdata_{0} AND manuscript_id:{1}'.format(type_singular, formatted_ids)
            else:
                delete_query = 'type:cantusdata_{0}'.format(type_singular)

            solr_conn.delete_query(delete_query)

            self.stdout.write('Re-adding {0} data... (may take a few minutes)'.format(type_singular))

            if not manuscript_ids:
                objects = model.objects.all()
            else:
                if model == Manuscript:
                    objects = model.objects.filter(id__in=manuscript_ids)
                else:
                    objects = model.objects.filter(manuscript__id__in=manuscript_ids)

            solr_records = []
            nb_obj = len(objects)
            for index, object in enumerate(objects):
                solr_records.append(object.create_solr_record())

                # Adding by blocks prevents out of memory errors
                if index > 0 and index % 500 == 0 or index == nb_obj - 1:
                    self.stdout.write("{0} / {1}".format(index + 1, nb_obj))
                    solr_conn.add_many(solr_records)
                    solr_records = []

        self.stdout.write('Committing changes...')
        solr_conn.commit()
        self.stdout.write('Done!')
