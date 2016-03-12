from rest_framework.response import Response
from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.models import Name
from neumeeditor.models.image import Image
from neumeeditor.serializers.glyph import GlyphSerializer
from neumeeditor.models.glyph import Glyph
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.renderers import JSONRenderer, JSONPRenderer, TemplateHTMLRenderer
from rest_framework.permissions import IsAuthenticated
from neumeeditor.serializers.image import ImageSerializer
from neumeeditor.serializers.name import NameSerializer


class GlyphList(generics.ListCreateAPIView):
    model = Glyph
    queryset = Glyph.objects.all()
    serializer_class = GlyphSerializer
    template_name = 'neumeeditor/index.html'
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        TemplateHTMLRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class GlyphDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Glyph
    queryset = Glyph.objects.all()
    serializer_class = GlyphSerializer
    template_name = 'neumeeditor/index.html'
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        TemplateHTMLRenderer)
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