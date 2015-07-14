from django.core.management.base import BaseCommand
from cantusdata.models.chant import Chant


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Run "python manage.py import_chant_data filename.csv" to import a chant
        file into the db.  filename.csv must exist in /public/data_dumps/.
        """

        import solr
        from cantusdata import settings

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        self.stdout.write('Flushing chant data...')
        solrconn.delete_query('type:cantusdata_chant')

        self.stdout.write('Re-adding chant data...')
        solrconn.add_many(chant.create_solr_record() for chant in Chant.objects.all())

        self.stdout.write('Comitting changes...')
        solrconn.commit()
