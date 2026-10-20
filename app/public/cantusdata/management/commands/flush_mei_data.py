from django.core.management.base import BaseCommand
from django.conf import settings

from cantusdata.helpers.solr_client import make_solr


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        self.stdout.write("Flushing music notation data from Solr...")
        solrconn = make_solr("admin", timeout=settings.SOLR_INDEX_TIMEOUT)
        solrconn.delete_query("type:cantusdata_music_notation")
        solrconn.commit()
        self.stdout.write("Success.")
