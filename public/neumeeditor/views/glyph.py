from rest_framework.response import Response
from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.models import Name
from neumeeditor.models.image import Image
from neumeeditor.serializers.glyph import GlyphSerializer
from neumeeditor.models.glyph import Glyph
from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import JSONRenderer, JSONPRenderer
from rest_framework.permissions import IsAuthenticated
from neumeeditor.serializers.image import ImageSerializer
from neumeeditor.serializers.name import NameSerializer


class GlyphListHTMLRenderer(CustomHTMLRenderer):
    template_name = "neumeeditor/index.html"


class GlyphDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "neumeeditor/index.html"


class GlyphList(generics.ListCreateAPIView):
    model = Glyph
    queryset = Glyph.objects.all()
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        GlyphListHTMLRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class GlyphDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Glyph
    queryset = Glyph.objects.all()
    serializer_class = GlyphSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        GlyphDetailHTMLRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class GlyphImages(generics.ListAPIView):
    serializer_class = ImageSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def get_queryset(self, glyph_id):
        return Image.objects.filter(glyph=glyph_id)

    def get(self, request, *args, **kwargs):
        glyph_id = kwargs['pk']
        # Get images for particular glyph
        serializer = self.serializer_class(self.get_queryset(glyph_id),
                                           many=True,
                                           context={'request': request})
        return Response(serializer.data)

class GlyphNames(generics.ListAPIView):
    serializer_class = NameSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def get_queryset(self, glyph_id):
        return Name.objects.filter(glyph=glyph_id)

    def get(self, request, *args, **kwargs):
        glyph_id = kwargs['pk']
        # Get images for particular glyph
        serializer = self.serializer_class(self.get_queryset(glyph_id),
                                           many=True,
                                           context={'request': request})
        return Response(serializer.data)