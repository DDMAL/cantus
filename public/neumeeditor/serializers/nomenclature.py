from neumeeditor.models.nomenclature import Nomenclature
from rest_framework import serializers


class NomenclatureSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Nomenclature
