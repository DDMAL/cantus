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

        if "image_uri" in kwargs:
            image_uri = kwargs["image_uri"]
            composed_request = f'''type:"cantusdata_folio" AND
                 manuscript_id:{manuscript_id} AND image_uri:"{image_uri}"'''
            result = solrconn.query(
                composed_request,
                sort="number asc",
                rows=2,
                fields=FOLIO_FIELDS,
                score=False,
            )

            if result.results:
                results_dict = {
                    key: [res[key] for res in result.results]
                    for key in result.results[0].keys()
                }
                return Response(results_dict)
            if result.numFound == 0:
                return Response({"number": None})
            raise Http404("Folio set query failed.")
        if "q" in request.GET:
            query_str = request.GET["q"]
            # Query for suggested folio numbers should return folios associated with
            # the manuscript that have the form:
            # [some number of leading zeros][the user-entered string][wildcard of characters].
            # Here we assume at most 3 leading zeros.
            composed_request = f"""type:"cantusdata_folio" AND manuscript_id:{manuscript_id} 
                                AND number_wo_lz:{query_str}*"""
            results = solrconn.query(
                composed_request,
                sort="number asc",
                rows=8,
                fields="number",
                score=False,
            )
            return Response(results)
        composed_request = f'type:"cantusdata_folio" AND manuscript_id:{manuscript_id}'
        results = solrconn.query(
            composed_request,
            sort="number asc",
            rows=1000,
            fields=FOLIO_FIELDS,
            score=False,
        )
        return Response(results)
