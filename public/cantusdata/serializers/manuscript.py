from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.chant import ChantSerializer
from rest_framework import serializers


class ManuscriptSerializer(serializers.HyperlinkedModelSerializer):
    chants = ChantSerializer(many=True, required=False)

    class Meta:
        model = Manuscript


class ManuscriptListSerializer(serializers.HyperlinkedModelSerializer):
    #chant_count = serializers.Field(source="chant_count")

    class Meta:
        model = Manuscript
        #fields = ('name', 'siglum', 'date', 'provenance', 'chant_count')