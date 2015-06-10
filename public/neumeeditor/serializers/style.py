from neumeeditor.models.style import Style
from rest_framework import serializers


class StyleSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Style
