from neumeeditor.helpers.authentication import ExpiringTokenAuthentication
from neumeeditor.models.image import Image
from neumeeditor.serializers.image import ImageSerializer
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, JSONPRenderer


class ImageList(generics.ListCreateAPIView):
    model = Image
    serializer_class = ImageSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class ImageDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Image
    serializer_class = ImageSerializer
    renderer_classes = (JSONRenderer, JSONPRenderer)
    authentication_classes = (ExpiringTokenAuthentication,
                              SessionAuthentication)
    permission_classes = (IsAuthenticated,)
