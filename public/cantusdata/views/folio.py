from cantusdata.models.folio import Folio
from cantusdata.serializers.concordance import ConcordanceSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class FolioListHTMLRenderer(CustomHTMLRenderer):
    template_name = "folio/folio_list.html"


class FolioDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "concordance/concordance_detail.html"


class FolioList(generics.ListCreateAPIView):
    model = Folio
    serializer_class = ConcordanceSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        FolioListHTMLRenderer)


class FolioDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Folio
    serializer_class = ConcordanceSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        FolioDetailHTMLRenderer)
