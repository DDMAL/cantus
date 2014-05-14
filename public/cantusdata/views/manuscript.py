from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.manuscript import ManuscriptSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class ManuscriptListHTMLRenderer(CustomHTMLRenderer):
    template_name = "manuscript/manuscript_list.html"


class ManuscriptDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "manuscript/manuscript_detail.html"


class ManuscriptList(generics.ListCreateAPIView):
    model = Manuscript
    serializer_class = ManuscriptSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, ManuscriptListHTMLRenderer)


class ManuscriptDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Manuscript
    serializer_class = ManuscriptSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, ManuscriptDetailHTMLRenderer)