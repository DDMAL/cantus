import time

from rest_framework.views import APIView
from rest_framework.response import Response

from cantusdata.serializers.search import SearchSerializer
from cantusdata.helpers.solrsearch import SolrSearch
from cantusdata.metrics.definitions import (
    SEARCH_REQUESTS,
    SEARCH_RESULT_OFFSET,
    SEARCH_RESULTS,
)
from cantusdata.metrics.events import elapsed_ms
from cantusdata.metrics.labels import (
    classify_client,
    parse_search_query,
    search_manuscript_id,
)
from cantusdata.metrics.search_log import log_search
from cantusdata.renderers import templated_view_renderers


class SearchView(APIView):
    serializer_class = SearchSerializer
    template_name = "require.html"
    renderer_classes = templated_view_renderers

    def get(self, request, *args, **kwargs):
        querydict = request.GET

        s = SolrSearch(request, {"public": "true"})

        if not querydict:
            return Response({"query": "", "numFound": 0, "results": []})

        # Search for fifteen rows by default
        s.solr_params.setdefault("rows", 15)

        # The client fetches a search's results a page at a time, so only the
        # first page counts as a search; later pages only record how deep
        # readers go.
        offset = s.solr_params.get("start", 0)
        SEARCH_RESULT_OFFSET.observe(offset)
        query = querydict.get("q", "")
        field, scope = parse_search_query(query)
        client = classify_client(request)
        started = time.perf_counter()
        try:
            search_results = s.search()
        except Exception:
            if not offset:
                SEARCH_REQUESTS.labels(field, scope, "error", client).inc()
            raise
        if not offset:
            num_found = search_results.numFound
            SEARCH_REQUESTS.labels(
                field, scope, "hits" if num_found else "no_hits", client
            ).inc()
            SEARCH_RESULTS.labels(field).observe(num_found)
            log_search(
                "chant",
                field=field,
                term=query,
                manuscript_id=search_manuscript_id(query),
                num_found=num_found,
                client=client,
                duration_ms=elapsed_ms(started),
            )

        result = {
            "query": querydict["q"],
            "numFound": search_results.numFound,
            "results": search_results,
        }

        result.update(s.solr_params)

        response = Response(result)
        return response
