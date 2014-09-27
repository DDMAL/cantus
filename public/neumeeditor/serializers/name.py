from neumeeditor.models.name import Name
from rest_framework import serializers


class NameSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()

    class Meta:
        model = Name
