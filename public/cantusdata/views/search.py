from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, JSONPRenderer

from cantusdata.serializers.search import SearchSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from cantusdata.helpers.solrsearch import SolrSearch


class SearchViewHTMLRenderer(CustomHTMLRenderer):
    template_name = "backbone.html"


class SearchView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, SearchViewHTMLRenderer)

    def get(self, request, *args, **kwargs):
        querydict = request.GET 
        if not querydict:
            return Response({'results': []})

        s = SolrSearch(request)

        search_results = s.search()
        result = {'results': search_results}
        response = Response(result)
        return response
