from neumeeditor.models.glyph import Glyph
from rest_framework import serializers
from neumeeditor.models.name import Name

class GlyphNameSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Name
        fields = ('string', 'short_code', 'glyph')


class GlyphSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()
    style = serializers.RelatedField(many=False, read_only=True)
    # name_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
    #                                                 view_name="name-detail")
    name_set = GlyphNameSetSerializer()
    image_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                   view_name="image-detail")

    class Meta:
        model = Glyph
