from django.core.management.base import BaseCommand
from django.conf import settings
import solr

class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        self.stdout.write("Flushing music notation data from Solr...")
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        solrconn.delete_query("type:cantusdata_music_notation")
        solrconn.commit()
        self.stdout.write("Success.")