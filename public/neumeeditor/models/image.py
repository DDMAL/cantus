from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import hashlib
from StringIO import StringIO
from PIL import Image as ImageModule
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from neumeeditor.helpers.file_system_utils import media_url_to_system_path, \
    remove_media_url
from neumeeditor.helpers.storage.media_file_system import media_file_name, \
    MediaFileSystemStorage


# A thumbnail should be 200 pixels tall
thumbnail_height = 200


class Image(models.Model):
    class Meta:
        app_label = "neumeeditor"

    image_file = models.ImageField(null=True, upload_to=media_file_name,
                                   storage=MediaFileSystemStorage())
    glyph = models.ForeignKey("neumeeditor.Glyph", null=True)
    md5sum = models.CharField(null=True, blank=True, max_length=36)

    @property
    def thumbnail(self):
        return generate_thumbnail_url(remove_media_url(self.image_file.url))

    def set_md5(self):
        md5 = hashlib.md5()
        for chunk in self.image_file.chunks():
            md5.update(chunk)
        self.md5sum = md5.hexdigest()

    def set_PIL_image(self, pil_image):
        file = StringIO()
        pil_image.save(file, format='png')
        self.image_file = InMemoryUploadedFile(file, None, 'foo.png', 'image/png',
                                               file.len, None)


def generate_thumbnail_url(image_url):
    """
    Generate an image thumbnail url.
    Ex: folder/image.png  ->  folder/image_thumbnail.png

    :param image_url:
    :return:
    """
    image_file_name, extension = os.path.splitext(image_url)
    return image_file_name + "_thumbnail" + extension

def get_thumbnail_dimensions(width, height):
    """
    Generate the thumbnail dimensions for an image.

    :param width: regular image width
    :param height: regular height
    :return:
    """
    new_width = int(float(thumbnail_height) / float(height) * float(width))
    return new_width, thumbnail_height

@receiver(pre_save, sender=Image)
def generate_hash(sender, instance, **kwargs):
    if not instance.pk:  # file is new
        instance.set_md5()

@receiver(post_save, sender=Image)
def save_thumbnails(sender, instance, **kwargs):
    # Get the old file system root
    old_url = media_url_to_system_path(instance.image_file.url)
    # Open the image and save the thumbnail
    image = ImageModule.open(old_url)
    width, height = image.size
    image.thumbnail(get_thumbnail_dimensions(width, height), ImageModule.ANTIALIAS)
    image.save(generate_thumbnail_url(old_url))
