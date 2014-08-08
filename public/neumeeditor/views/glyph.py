from neumeeditor.serializers.glyph import GlyphSerializer
from neumeeditor.models.glyph import Glyph
from rest_framework import generics
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class GlyphList(generics.ListCreateAPIView):
    model = Glyph
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class GlyphDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Glyph
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
