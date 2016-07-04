from rest_framework.views import APIView
from rest_framework.response import Response

from cantusdata.serializers.search import SearchSerializer
from cantusdata.helpers.solrsearch import SolrSearch
from cantusdata.renderers import templated_view_renderers


class SearchView(APIView):
    serializer_class = SearchSerializer
    template_name = 'require.html'
    renderer_classes = templated_view_renderers

    def get(self, request, *args, **kwargs):
        querydict = request.GET

        s = SolrSearch(request, {'public': 'true'})

        if not querydict:
            return Response({'query': '', 'numFound': 0, 'results': []})

        # Search for fifteen rows by default
        s.solr_params.setdefault('rows', 15)

        search_results = s.search()

        result = {
            'query': querydict['q'],
            'numFound': search_results.numFound,
            'results': search_results
        }

        result.update(s.solr_params)

        response = Response(result)
        return response
