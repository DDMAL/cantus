from neumeeditor.models.image import Image
from neumeeditor.models.glyph import Glyph
from rest_framework import serializers
from django.conf import settings
import os


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    # image_file = serializers.SerializerMethodField("retrieve_image_file")
    glyph = serializers.HyperlinkedRelatedField(view_name='glyph-detail',
                                                queryset=Glyph.objects.all())

    class Meta:
        model = Image

    # def retrieve_image_file(self, obj):
        # request = self.context.get('request', None)
        # path = os.path.relpath(obj.image_file.path, settings.MEDIA_ROOT)
        # url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL_NEUMEEDITOR, path))
        # return url
