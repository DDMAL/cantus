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

        s = SolrSearch(request)
        facets = s.facets(['name', 'siglum', 'date', 'provenance', 'mode',
                           'manuscript', 'marginalia', 'folio', 'sequence',
                           'feast', 'office', 'genre', 'position',
                           'differentia', 'finalis'])

        if not querydict:
            return Response({'numFound': 0, 'results': [],
                             'facets': facets.facet_counts})

        search_results = s.search(rows=10)
        result = dict({'numFound': search_results.numFound,
                  'results': search_results,
                  'facets': facets.facet_counts}.items()
                      + s.solr_params.items())
        response = Response(result)
        return response
