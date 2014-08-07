from neumeeditor.serializers.name import NameSerializer
from neumeeditor.models.name import Name
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class NameList(generics.ListCreateAPIView):
    model = Name
    serializer_class = NameSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)


class NameDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Name
    serializer_class = NameSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
