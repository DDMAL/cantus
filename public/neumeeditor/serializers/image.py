from neumeeditor.models.image import Image
from neumeeditor.models.glyph import Glyph
from rest_framework import serializers


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    # image_file = serializers.SerializerMethodField("retrieve_image_file")
    image_file = serializers.ImageField(allow_empty_file=False, use_url=False)
    glyph = serializers.HyperlinkedRelatedField(view_name='glyph-detail',
                                                queryset=Glyph.objects.all())
    # thumbnail = serializers.ReadOnlyField()

    class Meta:
        model = Image
        # fields = ('url', 'id', 'image_file', 'glyph', 'thumbnail')

    # def retrieve_image_file(self, obj):
    #     request = self.context.get('request', None)
    #     path = os.path.relpath(obj.image_file.path, settings.MEDIA_ROOT)
    #     url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL_NEUMEEDITOR, path))
    #     return url
