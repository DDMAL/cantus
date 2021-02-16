from django.conf import settings
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from cantusdata.serializers.search import SearchSerializer
import solr


FOLIO_FIELDS = [
    "type",
    "number",
    "image_uri",
    "item_id",
    "manuscript_id",
]


class ManuscriptFolioSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        manuscript_id = kwargs["pk"]

        if "image_uri" in kwargs:
            image_uri = kwargs["image_uri"]
            composed_request = 'type:"cantusdata_folio" AND manuscript_id:{0} AND image_uri:"{1}"'.format(
                manuscript_id, image_uri
            )

            result = solrconn.query(
                composed_request,
                sort="number asc",
                rows=1,
                fields=FOLIO_FIELDS,
                score=False,
            )

            # We only want the single result!
            # TODO: Figure out the best way to handle this
            if result.results:
                return Response(result.results[0])
            else:
                raise Http404("No data for a folio with that number")
        else:
            composed_request = (
                'type:"cantusdata_folio" AND manuscript_id:{0}'.format(
                    manuscript_id
                )
            )
            results = solrconn.query(
                composed_request,
                sort="number asc",
                rows=1000,
                fields=FOLIO_FIELDS,
                score=False,
            )
            return Response(results)
