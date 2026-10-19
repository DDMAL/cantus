from django.core.management.base import BaseCommand
from django.conf import settings

from cantusdata.helpers.solr_client import make_solr


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        self.stdout.write("Flushing chant data from Solr...")
        solrconn = make_solr("admin", timeout=settings.SOLR_INDEX_TIMEOUT)
        # Kill chants
        solrconn.delete_query("type:cantusdata_chant")
        solrconn.commit()
        # Kill folios
        self.stdout.write("Flushing folio data from Solr...")
        solrconn.delete_query("type:cantusdata_folio")
        # Kill manuscripts
        self.stdout.write("Flushing manuscript data from Solr...")
        solrconn.delete_query("type:cantusdata_manuscript")
        solrconn.commit()
        self.stdout.write("Success.")
