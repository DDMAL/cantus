from neumeeditor.serializers.style import StyleSerializer
from neumeeditor.models.style import Style
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class StyleList(generics.ListCreateAPIView):
    model = Style
    serializer_class = StyleSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


class StyleDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Style
    serializer_class = StyleSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
