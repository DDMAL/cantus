from neumeeditor.models.image import Image
from rest_framework import serializers


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()

    class Meta:
        model = Image
