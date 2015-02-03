from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.serializers.style import StyleSerializer
from neumeeditor.models.style import Style
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class StyleList(generics.ListCreateAPIView):
    model = Style
    serializer_class = StyleSerializer
    queryset = Style.objects.all()
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class StyleDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Style
    serializer_class = StyleSerializer
    queryset = Style.objects.all()
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)
