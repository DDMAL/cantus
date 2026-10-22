import re
import time

import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from cantusdata.helpers.solr_client import solr_get
from cantusdata.metrics.definitions import SUGGEST_REQUESTS
from cantusdata.metrics.events import elapsed_ms
from cantusdata.metrics.labels import classify_client
from cantusdata.metrics.search_log import log_search

SUGGESTION_FIELDS = ("office", "genre", "feast")
# '*' across all manuscripts; otherwise an id, which the client sends quoted.
_MANUSCRIPT_ID = re.compile(r'^\*$|^"?(\d+)"?$')


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
        missing = [
            name for name in ("q", "field", "manuscript_id") if name not in request.GET
        ]
        if missing:
            return self._bad_request(f"Missing parameter(s): {', '.join(missing)}.")

        query = request.GET["q"]
        field = request.GET["field"]
        if field not in SUGGESTION_FIELDS:
            return self._bad_request(
                f"field must be one of {', '.join(SUGGESTION_FIELDS)}."
            )
        match = _MANUSCRIPT_ID.match(request.GET["manuscript_id"])
        if match is None:
            return self._bad_request("manuscript_id must be a manuscript id or '*'.")
        manuscript_id = match.group(1) or "*"

        started = time.perf_counter()
        try:
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
        except requests.RequestException:
            results = None
        succeeded = results is not None and results.status_code == 200
        SUGGEST_REQUESTS.labels(field, "success" if succeeded else "error").inc()
        if not succeeded:
            return Response(
                {"detail": "Suggestions are unavailable right now."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
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

    @staticmethod
    def _bad_request(detail: str) -> Response:
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
