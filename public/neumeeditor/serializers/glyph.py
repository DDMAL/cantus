from neumeeditor.models.glyph import Glyph
from rest_framework import serializers


class GlyphSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()

    class Meta:
        model = Glyph
