from cantusdata.models.manuscript import Manuscript
from cantusdata.serializers.chant import ChantSerializer
from cantusdata.serializers.neume_exemplar import NeumeExemplarSerializer
from rest_framework import serializers


class ManuscriptSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    siglum_slug = serializers.SlugField()
    plugins = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="slug"
    )

    neume_exemplars = NeumeExemplarSerializer(many=True, read_only=True)

    class Meta:
        model = Manuscript
        fields = "__all__"


class ManuscriptListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Manuscript
        fields = (
            "name",
            "url",
            "id",
            "siglum",
            "siglum_slug",
            "date",
            "provenance",
            "folio_count",
            "chant_count",
            "cantus_url",
            "manifest_url",
        )
