from django.core.management.base import BaseCommand
from django.conf import settings
import solr

class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        records = solrconn.query("type:cantusdata_music_notation")
        total = 0
        while records.numFound > 0:
            records = solrconn.query("type:cantusdata_music_notation", rows=250)
            for result in records.results:
                solrconn.delete(result['id'])
                solrconn.commit()
                total += 1
            self.stdout.write("Flushed {0} elements from Solr.".format(total))

        self.stdout.write("Flushed {0} elements from Solr.".format(total))