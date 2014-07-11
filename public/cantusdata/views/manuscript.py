from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.manuscript import ManuscriptSerializer
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class ManuscriptListHTMLRenderer(CustomHTMLRenderer):
    template_name = "backbone.html"


class ManuscriptDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "backbone.html"


class ManuscriptHasChantsMixin(object):
    """
    This Mixin filters out manuscripts that have no chants.
    """
    def get_queryset(self):
        queryset = Manuscript.objects.all()
        return queryset.filter(chant_count__gt=0)


class ManuscriptList(ManuscriptHasChantsMixin, generics.ListCreateAPIView):
    model = Manuscript
    serializer_class = ManuscriptSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        ManuscriptListHTMLRenderer)


class ManuscriptDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Manuscript
    serializer_class = ManuscriptSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        ManuscriptDetailHTMLRenderer)
