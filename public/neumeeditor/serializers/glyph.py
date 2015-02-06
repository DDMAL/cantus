from neumeeditor.models.glyph import Glyph
from rest_framework import serializers
from neumeeditor.models.name import Name
from neumeeditor.serializers.image import ImageSerializer


class GlyphNameSetSerializer(serializers.HyperlinkedModelSerializer):
    # glyph = serializers.HyperlinkedIdentityField(view_name='glyph-detail')
    # glyph = serializers.StringRelatedField()
    class Meta:
        model = Name
        fields = ('id', 'url', 'string', 'glyph')


class GlyphSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    style = serializers.StringRelatedField(
        # many=False,
        read_only=True)

    name_set = GlyphNameSetSerializer(many=True, read_only=True)
    image_set = ImageSerializer(many=True, read_only=True)
    # name_set = serializers.HyperlinkedRelatedField(many=True, view_name='name-detail', read_only=True)
    # image_set = serializers.HyperlinkedRelatedField(many=True, view_name='image-detail', read_only=True)

    class Meta:
        model = Glyph
