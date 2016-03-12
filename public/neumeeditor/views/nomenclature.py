from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.models import Name
from neumeeditor.serializers.name import NameSerializer
from neumeeditor.models.nomenclature import Nomenclature
from neumeeditor.serializers.nomenclature import NomenclatureSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, JSONPRenderer, TemplateHTMLRenderer


class NomenclatureList(generics.ListCreateAPIView):
    model = Nomenclature
    serializer_class = NomenclatureSerializer
    template_name = "neumeeditor/index.html"
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        TemplateHTMLRenderer)
    queryset = Nomenclature.objects.all()
    # authentication_classes = (ExpiringTokenAuthentication,
    #                           SessionAuthentication)
    # permission_classes = (IsAuthenticated,)


class NomenclatureDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Nomenclature
    serializer_class = NomenclatureSerializer
    template_name = "neumeeditor/index.html"
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        TemplateHTMLRenderer)
    queryset = Nomenclature.objects.all()
    # authentication_classes = (SessionAuthentication,)
    # permission_classes = (IsAuthenticated,)


class NomenclatureNames(generics.ListAPIView):
    serializer_class = NameSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)

    def get_queryset(self, nomenclature_id):
        return Name.objects.filter(nomenclatures=nomenclature_id)

    def get(self, request, *args, **kwargs):
        nomenclature_id = kwargs['pk']
        # Get images for particular glyph
        serializer = self.serializer_class(self.get_queryset(nomenclature_id),
                                           many=True,
                                           context={'request': request})
        return Response(serializer.data)
