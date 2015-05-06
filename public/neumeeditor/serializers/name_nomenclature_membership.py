from rest_framework import serializers
from neumeeditor.models.name_nomenclature_membership import NameNomenclatureMembership


class NameNomenclatureMembershipSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    name_string = serializers.ReadOnlyField()
    nomenclature_string = serializers.ReadOnlyField()

    class Meta:
        model = NameNomenclatureMembership
