from django.conf import settings
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from cantusdata.serializers.search import SearchSerializer
import solr


FOLIO_FIELDS = [
    "type",
    "number",
    "image_uri",
    "item_id",
    "manuscript_id",
]


class ManuscriptFolioSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        solrconn = solr.SolrConnection(settings.SOLR_SERVER)

        manuscript_id = kwargs["pk"]

        # If the request contains an image_uri parameter, return the folio(s)
        # associated with that image.
        if "image_uri" in kwargs:
            image_uri = kwargs["image_uri"]
            composed_request = f'''type:"cantusdata_folio" AND
                 manuscript_id:{manuscript_id} AND image_uri:"{image_uri}"'''
            results = solrconn.query(
                composed_request,
                sort="number asc",
                rows=2,
                fields=FOLIO_FIELDS,
                score=False,
            )
            if results.numFound > 0:
                # Initialize combined results dict with the first result
                combined_results = results.results[0]
                # For manuscripts with double-folio images, add the possible
                # second folio to the combined results dict.
                if results.numFound == 2:
                    for field in FOLIO_FIELDS:
                        combined_results[field] = [
                            combined_results[field],
                            results.results[1][field],
                        ]
                return Response(combined_results)
            if results.numFound == 0:
                return Response({"number": None})
            raise Http404("Folio set query failed.")
        # If a query parameter is passed, return suggested folios
        # for navigation.
        if "q" in request.GET:
            query_str = request.GET["q"]
            # Query for suggested folio numbers should return folios associated with
            # the manuscript that have the form:
            # [some number of leading zeros][the user-entered string][wildcard of characters].
            composed_request = f"""type:"cantusdata_folio" AND manuscript_id:{manuscript_id}
                                AND number_wo_lead_zero:{query_str}*"""
            results = solrconn.query(
                composed_request,
                sort="number asc",
                rows=8,
                fields="number",
                score=False,
            )
            return Response(results)
        # Otherwise, simply return the given manuscript's folios.
        composed_request = f'type:"cantusdata_folio" AND manuscript_id:{manuscript_id}'
        results = solrconn.query(
            composed_request,
            sort="number asc",
            rows=1000,
            fields=FOLIO_FIELDS,
            score=False,
        )
        return Response(results)
