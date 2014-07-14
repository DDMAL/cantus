from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.chant import ChantSerializer
from rest_framework import serializers


class ManuscriptSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()
    # chants = ChantSerializer(many=True, required=False)
    folio_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                view_name="folio-detail")
    # chant_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
    #                                             view_name="chant-detail")
    siglum_slug = serializers.Field()
    plugins = serializers.SlugRelatedField(many=True, read_only=True,
                                           slug_field='slug')

    class Meta:
        model = Manuscript


class ManuscriptListSerializer(serializers.HyperlinkedModelSerializer):
    #chant_count = serializers.Field(source="chant_count")

    class Meta:
        model = Manuscript
        #fields = ('name', 'siglum', 'date', 'provenance', 'chant_count')
