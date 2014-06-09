from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from cantusdata.serializers.search import SearchSerializer
import solr


class FolioChantSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def get(self, request, *args, **kwargs):
        folio_id = kwargs['pk']
        # We want to get all chants of a particular folio of a particular
        # manuscript.  It is fastest to pull these from Solr!
        composed_request = u'type:"cantusdata_chant" AND folio_id:{0}'.format(folio_id)
        # Connect to Solr
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        # Query
        result = solrconn.query(composed_request, sort="sequence asc")
        return Response(result)
