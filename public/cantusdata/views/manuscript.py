from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.manuscript import ManuscriptSerializer, ManuscriptListSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class ManuscriptListHTMLRenderer(CustomHTMLRenderer):
    template_name = "require.html"


class ManuscriptDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "require.html"


class ManuscriptList(generics.ListCreateAPIView):
    model = Manuscript
    queryset = Manuscript.objects.all()
    serializer_class = ManuscriptListSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        ManuscriptListHTMLRenderer)

    def get_queryset(self):
        return Manuscript.objects.filter(public=True)


class ManuscriptDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Manuscript
    queryset = Manuscript.objects.all()
    serializer_class = ManuscriptSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        ManuscriptDetailHTMLRenderer)
