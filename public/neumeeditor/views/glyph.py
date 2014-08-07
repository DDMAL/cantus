from neumeeditor.serializers.glyph import GlyphSerializer
from neumeeditor.models.glyph import Glyph
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class GlyphList(generics.ListCreateAPIView):
    model = Glyph
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)


class GlyphDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Glyph
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
