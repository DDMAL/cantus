from cantusdata.models.concordance import Concordance
from cantusdata.serializers.concordance import ConcordanceSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class ConcordanceListHTMLRenderer(CustomHTMLRenderer):
    template_name = "concordance/concordance_list.html"


class ConcordanceDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "concordance/concordance_detail.html"


class ConcordanceList(generics.ListCreateAPIView):
    model = Concordance
    serializer_class = ConcordanceSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
                        # ConcordanceListHTMLRenderer)


class ConcordanceDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Concordance
    serializer_class = ConcordanceSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
                        # ConcordanceDetailHTMLRenderer)
