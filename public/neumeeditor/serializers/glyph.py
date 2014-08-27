from neumeeditor.models.glyph import Glyph
from rest_framework import serializers


class GlyphSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.Field()
    style = serializers.RelatedField(many=False, read_only=True)
    name_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                    view_name="name-detail")
    image_set = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                   view_name="image-detail")

    class Meta:
        model = Glyph
