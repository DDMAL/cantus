from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings

import solr
import requests


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

        solr_server = settings.SOLR_SERVER
        results = requests.get(
            f"{solr_server}/select",
            params={
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
        if results.status_code == 200:
            facet_counts = results.json()["facet_counts"]["facet_fields"][field]
            # The names of the facets (ie. the suggestions) are in the even indices of the list
            facet_counts = facet_counts[::2]
            response = Response(facet_counts)
            return response
