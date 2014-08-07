from neumeeditor.models.style import Style
from rest_framework import serializers


class StyleSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()

    class Meta:
        model = Style
