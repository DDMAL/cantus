from cantusdata.models.chant import Chant
from cantusdata.serializers.chant import ChantSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class ChantListHTMLRenderer(CustomHTMLRenderer):
    template_name = "chant/chant_list.html"


class ChantDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "chant/chant_detail.html"


class ChantList(generics.ListCreateAPIView):
    model = Chant
    serializer_class = ChantSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, ChantListHTMLRenderer)


class ChantDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Chant
    serializer_class = ChantSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, ChantDetailHTMLRenderer)