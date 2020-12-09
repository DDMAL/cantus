from django.core.management.base import BaseCommand
from django.conf import settings
import solr


class Command(BaseCommand):
    args = ""

    def handle(self, *args, **kwargs):
        # Grab the manuscript name
        manuscript = args[0]

        if manuscript == "salzinnes":
            siglum = "cdn-hsmu-m2149l4"
        elif manuscript == "st_gallen_390":
            siglum = "ch-sgs-390"
        elif manuscript == "st_gallen_391":
            siglum = "ch-sgs-391"
        else:
            raise Exception("Please provide manuscript name!")

        self.stdout.write(
            "Removing {0} music notation data from Solr...".format(manuscript)
        )
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        solrconn.delete_query(
            "type:cantusdata_music_notation AND siglum_slug:{0}".format(siglum)
        )
        solrconn.commit()
        self.stdout.write("Success.")