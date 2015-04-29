from cantusdata.renderers.custom_html_renderer import CustomHTMLRenderer
from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.serializers.name import NameSerializer
from neumeeditor.models.nomenclature import Nomenclature
from neumeeditor.serializers.nomenclature import NomenclatureSerializer
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class NomenclatureListHTMLRenderer(CustomHTMLRenderer):
    template_name = "neumeeditor/index.html"


class NomenclatureDetailHTMLRenderer(CustomHTMLRenderer):
    template_name = "neumeeditor/index.html"


class NomenclatureList(generics.ListCreateAPIView):
    model = Nomenclature
    serializer_class = NomenclatureSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        NomenclatureListHTMLRenderer)
    queryset = Nomenclature.objects.all()
    # authentication_classes = (ExpiringTokenAuthentication,
    #                           SessionAuthentication)
    # permission_classes = (IsAuthenticated,)


class NomenclatureDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Nomenclature
    serializer_class = NomenclatureSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer,
                        NomenclatureDetailHTMLRenderer)
    queryset = Nomenclature.objects.all()
    # authentication_classes = (SessionAuthentication,)
    # permission_classes = (IsAuthenticated,)
