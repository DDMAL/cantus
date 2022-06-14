from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
# from rest_framework_jsonp.renderers import JSONPRenderer
from cantusdata.serializers.search import SearchSerializer
import solr


CHANT_FIELDS = [
    "type",
    "item_id",
    "marginalia",
    "manuscript",
    "manuscript_id",
    "manuscript_name_hidden",
    "folio",
    "folio_id",
    "sequence",
    "cantus_id",
    "feast",
    "office",
    "genre",
    "position",
    "mode",
    "differentia",
    "finalis",
    "incipit",
    "full_text",
    "volpiano",
    "concordances",
]


class FolioChantSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        folio_id = kwargs["pk"]
        # We want to get all chants of a particular folio of a particular
        # manuscript.  It is fastest to pull these from Solr!
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        composed_request = 'type:"cantusdata_chant" AND folio_id:{0}'.format(
            folio_id
        )
        results = solrconn.query(
            composed_request,
            sort="sequence asc",
            rows=100,
            fields=CHANT_FIELDS,
            score=False,
        )

        return Response(results)


class ManuscriptChantSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        manuscript_id = kwargs["pk"]

        if "start" in kwargs:
            start = kwargs["start"]
        else:
            start = 0

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        composed_request = (
            'type:"cantusdata_chant" AND manuscript_id:{0}'.format(
                manuscript_id
            )
        )
        results = solrconn.query(
            composed_request,
            sort="sequence asc",
            start=start,
            rows=100,
            fields=CHANT_FIELDS,
            score=False,
        )

        return Response(results)
