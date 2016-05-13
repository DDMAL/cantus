from django.core.management.base import BaseCommand
from cantusdata.models.manuscript import Manuscript


class Command(BaseCommand):
    def handle(self, *args, **options):
        import solr
        from cantusdata import settings

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        self.stdout.write('Flushing manuscript data...')
        solrconn.delete_query('type:cantusdata_manuscript')

        self.stdout.write('Re-adding manuscript data...')

        solrconn.add_many(manuscript.create_solr_record() for manuscript in Manuscript.objects.all())

        self.stdout.write('Comitting changes...')
        solrconn.commit()
