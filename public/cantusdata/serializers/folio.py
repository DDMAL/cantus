from cantusdata.models.folio import Folio
from rest_framework import serializers


class FolioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Folio