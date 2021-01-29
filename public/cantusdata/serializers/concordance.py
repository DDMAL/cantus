from cantusdata.models.concordance import Concordance
from rest_framework import serializers


class ConcordanceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Concordance
        fields = '__all__'
