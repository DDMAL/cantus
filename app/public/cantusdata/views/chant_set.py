from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer

# from rest_framework_jsonp.renderers import JSONPRenderer
from cantusdata.serializers.search import SearchSerializer
from cantusdata.helpers.solr_client import make_solr
from cantusdata.metrics.definitions import FOLIO_CHANT_LOOKUPS
from cantusdata.metrics.labels import OTHER, manuscript_label
from cantusdata.models.folio import Folio

CHANT_FIELDS = [
    "type",
    "item_id",
    "marginalia",
    "manuscript",
    "manuscript_id",
    "manuscript_name_hidden",
    "folio",
    "folio_id",
    "sequence",
    "cantus_id",
    "feast",
    "office",
    "genre",
    "position",
    "mode",
    "differentia",
    "differentiae_database",
    "finalis",
    "incipit",
    "full_text",
    "full_text_ms",
    "volpiano",
    "cdb_uri",
]


class FolioChantSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        folio_ids_list = [f"folio_id:{id}" for id in kwargs["pk"].split(",")]
        folio_ids_str = " OR ".join(folio_ids_list)
        # We want to get all chants of a particular folio of a particular
        # manuscript.  It is fastest to pull these from Solr!
        solrconn = make_solr("chant_set")
        composed_request = f'type:"cantusdata_chant" AND ({folio_ids_str})'
        results = solrconn.query(
            composed_request,
            sort="folio asc, sequence asc",
            rows=100,
            fields=CHANT_FIELDS,
            score=False,
        )
        FOLIO_CHANT_LOOKUPS.labels(
            self._manuscript_label(results, kwargs["pk"]),
            "true" if results.numFound else "false",
        ).inc()

        return Response(results)

    @staticmethod
    def _manuscript_label(results, folio_ids: str) -> str:
        if results.results:
            return manuscript_label(results.results[0]["manuscript_id"])
        # No chants to read it from, so ask the folio.
        first_id = folio_ids.split(",")[0]
        if not first_id.isdigit():
            return OTHER
        manuscript_id = (
            Folio.objects.filter(pk=first_id)
            .values_list("manuscript_id", flat=True)
            .first()
        )
        return manuscript_label(manuscript_id) if manuscript_id else OTHER


class ManuscriptChantSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        manuscript_id = kwargs["pk"]

        if "start" in kwargs:
            start = kwargs["start"]
        else:
            start = 0

        solrconn = make_solr("chant_set")

        composed_request = 'type:"cantusdata_chant" AND manuscript_id:{0}'.format(
            manuscript_id
        )
        results = solrconn.query(
            composed_request,
            sort="sequence asc",
            start=start,
            rows=100,
            fields=CHANT_FIELDS,
            score=False,
        )

        return Response(results)
