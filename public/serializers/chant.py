from cantusdata.models.chant import Chant
from rest_framework import serializers


class ChantSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Chant