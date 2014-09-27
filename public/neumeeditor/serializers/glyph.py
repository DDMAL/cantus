from neumeeditor.models.glyph import Glyph
from rest_framework import serializers
from neumeeditor.models.name import Name
from neumeeditor.models.image import Image
from neumeeditor.serializers.image import ImageSerializer


class GlyphNameSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Name
        fields = ('id', 'url', 'string', 'glyph')


class GlyphSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()
    style = serializers.RelatedField(many=False, read_only=True)
    name_set = GlyphNameSetSerializer()
    image_set = ImageSerializer()

    class Meta:
        model = Glyph
