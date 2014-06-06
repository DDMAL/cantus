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
        querydict = request.GET
        if not querydict:
            return Response([])

        print request.GET
        manuscript = request.GET.get(u"manuscript")
        folio = request.GET.get(u"folio")



        # We want to get all chants of a particular folio of a particular
        # manuscript.  It is fastest to pull these from Solr!
        composed_request = u'type:"cantusdata_chant" AND manuscript:"{0}" AND folio:"{1}"'.format(manuscript, folio)

        # Connect to Solr
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        # Query
        result = solrconn.query(composed_request)


        # search_results = s.search(q=u'type:"cantusdata_chant')
        # result = {'results': search_results}
        response = Response(result)
        return response
