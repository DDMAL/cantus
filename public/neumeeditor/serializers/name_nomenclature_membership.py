from rest_framework import serializers
from neumeeditor.models.name_nomenclature_membership import NameNomenclatureMembership


class NameNomenclatureMembershipSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = NameNomenclatureMembership
