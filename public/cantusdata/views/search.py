from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, JSONPRenderer

from cantusdata.serializers.search import SearchSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
import solr


class SearchViewHTMLRenderer(CustomHTMLRenderer):
    template_name = "backbone.html"


class SearchView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, SearchViewHTMLRenderer)

    def get(self, request, *args, **kwargs):
        querydict = request.GET 
        if not querydict:
            return Response({'results': []})

        query = ""
        start = 0

        if 'q' in querydict:
            query = querydict.get('q')
        if 'start' in querydict:
            start = querydict.get('start')

        composed_request = u"{0}".format(query)

        solrconn = solr.SolrConnection(settings.SOLR_SERVER)
        result = solrconn.query(composed_request, start=start, rows=10)

        # print result

        return Response({'results': result})
