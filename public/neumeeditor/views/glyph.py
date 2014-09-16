from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.serializers.glyph import GlyphSerializer
from neumeeditor.models.glyph import Glyph
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.permissions import IsAuthenticated


class GlyphListHTMLRenderer(CustomHTMLRenderer):
    template_name = "neumeeditor/index.html"


class GlyphDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "neumeeditor/index.html"


class GlyphList(generics.ListCreateAPIView):
    model = Glyph
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, GlyphListHTMLRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class GlyphDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Glyph
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer, GlyphDetailHTMLRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)
