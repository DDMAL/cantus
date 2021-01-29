from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
# from rest_framework_jsonp.renderers import JSONPRenderer
from cantusdata.models import Manuscript
from cantusdata.serializers.search import SearchSerializer
from cantusdata.helpers.solrsearch import SolrSearchQueryless


class ManuscriptGlyphSetView(APIView):
    serializer_class = SearchSerializer
    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        manuscript = Manuscript.objects.get(id=kwargs["pk"])
        result = (
            SolrSearchQueryless(
                'q=type%3Acantusdata_music_notation+AND+siglum_slug%3A"{0}"'.format(
                    manuscript.siglum_slug
                )
            )
            .facets(["neumes"])
            .facet_counts["facet_fields"]["neumes"]
        )
        return Response(result)
