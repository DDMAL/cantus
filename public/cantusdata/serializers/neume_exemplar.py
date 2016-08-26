from cantusdata.models.neume_exemplar import NeumeExemplar
from rest_framework import serializers


class NeumeExemplarSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeumeExemplar
        fields = ('name', 'siglum_slug', 'p', 'x', 'y', 'w', 'h')

    siglum_slug = serializers.SlugField(source='folio.manuscript.siglum_slug')

    # These short forms match the values given in the boxes
    # in Solr OMR results
    p = serializers.CharField(source='folio.image_uri')
    x = serializers.IntegerField(source='x_coord')
    y = serializers.IntegerField(source='y_coord')
    w = serializers.IntegerField(source='width')
    h = serializers.IntegerField(source='height')
