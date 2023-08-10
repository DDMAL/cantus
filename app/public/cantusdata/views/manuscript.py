from rest_framework import generics
from django.views import generic
from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.manuscript import (
    ManuscriptSerializer,
    ManuscriptListSerializer,
)
from cantusdata.renderers import templated_view_renderers


class ManuscriptList(generics.ListAPIView):
    model = Manuscript
    queryset = Manuscript.objects.filter(public=True)
    serializer_class = ManuscriptListSerializer
    template_name = "require.html"
    renderer_classes = templated_view_renderers


class ManuscriptDetail(generics.RetrieveAPIView):
    model = Manuscript
    queryset = Manuscript.objects.filter(public=True)
    serializer_class = ManuscriptSerializer
    template_name = "require.html"
    renderer_classes = templated_view_renderers
