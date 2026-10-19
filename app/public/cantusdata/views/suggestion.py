import time

from rest_framework.views import APIView
from rest_framework.response import Response

from cantusdata.helpers.solr_client import solr_get
from cantusdata.metrics.definitions import SUGGEST_REQUESTS
from cantusdata.metrics.events import elapsed_ms
from cantusdata.metrics.labels import classify_client
from cantusdata.metrics.search_log import log_search


class SuggestionView(APIView):
    """
    A view providing search suggestions. Currently,
     suggestions are only provided for the following fields:
     - office
     - genre
     - feast

     For these fields, the suggestions are provided by facet counts.
    """

    def get(self, request, *args, **kwargs):
        if not ("q" in request.GET and "field" in request.GET):
            return Response()

        query = request.GET["q"]
        field = request.GET["field"]
        manuscript_id = request.GET[
            "manuscript_id"
        ]  # '*' when searching through all manuscripts

        if field not in ["office", "genre", "feast"]:
            return Response()

        started = time.perf_counter()
        results = solr_get(
            "suggest",
            {
                "q": "*:*",
                "rows": 0,
                "facet": "true",
                "fq": f"manuscript_id:{manuscript_id}",
                "facet.field": field,
                "facet.limit": 8,
                "facet.contains": query,
                "facet.contains.ignoreCase": "true",
            },
        )
        SUGGEST_REQUESTS.labels(
            field, "success" if results.status_code == 200 else "error"
        ).inc()
        if results.status_code == 200:
            facet_counts = results.json()["facet_counts"]["facet_fields"][field]
            # The names of the facets (ie. the suggestions) are in the even indices of the list
            facet_counts = facet_counts[::2]
            suggestion_objs = [{"term": term} for term in facet_counts]
            log_search(
                "suggest",
                field=field,
                term=query,
                manuscript_id=None if manuscript_id == "*" else manuscript_id,
                num_found=len(suggestion_objs),
                client=classify_client(request),
                duration_ms=elapsed_ms(started),
            )
            return Response(suggestion_objs)
