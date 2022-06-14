from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings

import solr


class SuggestionView(APIView):
    def get(self, request, *args, **kwargs):

        if not ("q" in request.GET and "dictionary" in request.GET):
            return Response()

        q = "{0}".format(request.GET["q"])
        dictionary = "{0}".format(request.GET["dictionary"])  # The suggester to use
        manuscript = "{0}".format(
            request.GET["manuscript"]
        )  # Can be '*' when searching through all manuscripts

        connection = solr.Solr(settings.SOLR_SERVER)
        search_handler = solr.SearchHandler(connection, "/suggest")

        # TODO fix solr so that the suggesters work with a context field (cfq)]
        # search_results = search_handler(q=q, suggest_dictionary=dictionary, suggest_cfq=manuscript)
        search_results = search_handler(q=q, suggest_dictionary=dictionary)

        results = search_results.suggest[dictionary][q]

        # Remove duplicates from the suggestions and limits the return number to 10
        results["suggestions"] = self._get_filtered_results(results["suggestions"])

        response = Response(results)
        return response

    def _get_filtered_results(self, suggestions):
        results = []
        for suggestion in suggestions:

            unique = True

            for result in results:
                if suggestion["term"] == result["term"]:
                    unique = False
                    break

            if unique:
                results.append(suggestion)

            if len(results) == 10:
                break

        return results
