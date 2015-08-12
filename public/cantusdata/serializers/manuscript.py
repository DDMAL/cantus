from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.chant import ChantSerializer
from cantusdata.serializers.neume_exemplar import NeumeExemplarSerializer
from rest_framework import serializers


class ManuscriptSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    # chants = ChantSerializer(many=True, required=False)
    folio_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                view_name="folio-detail")
    # chant_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
    #                                             view_name="chant-detail")
    siglum_slug = serializers.SlugField()
    plugins = serializers.SlugRelatedField(many=True, read_only=True,
                                           slug_field='slug')

    neume_exemplars = NeumeExemplarSerializer(many=True, read_only=True)

    class Meta:
        model = Manuscript


class ManuscriptListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Manuscript
        fields = ('name', 'url', 'id', 'siglum', 'siglum_slug', 'date', 'provenance', 'chant_count')
