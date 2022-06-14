from cantusdata.models.folio import Folio
from rest_framework import serializers


class FolioSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Folio
        fields = "__all__"

    # chant_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
    #                                            view_name="chant-detail")
