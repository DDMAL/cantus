from cantusdata.models.chant import Chant
from rest_framework import serializers


class ChantSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Chant
        fields = "__all__"
