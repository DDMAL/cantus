import os
import hashlib
from PIL import Image as ImageModule
from django.db import models
from django.db.models.signals import post_save, post_delete
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

    def save(self, *args, **kwargs):
        if not self.pk:  # file is new
            md5 = hashlib.md5()
            for chunk in self.image_file.chunks():
                md5.update(chunk)
            self.md5sum = md5.hexdigest()
        super(Image, self).save(*args, **kwargs)



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
    print "W: {0} H: {1}".format(width, height)
    new_width = int(float(thumbnail_height) / float(height) * float(width))
    print "TEST: {0} {1} ".format(thumbnail_height / height, thumbnail_height)
    print "W: {0} H: {1}".format(new_width, thumbnail_height)
    return new_width, thumbnail_height

@receiver(post_save, sender=Image)
def save_thumbnails(sender, instance, **kwargs):
    # Get the old file system root
    old_url = media_url_to_system_path(instance.image_file.url)
    # Open the image and save the thumbnail
    image = ImageModule.open(old_url)
    width, height = image.size
    image.thumbnail(get_thumbnail_dimensions(width, height), ImageModule.ANTIALIAS)
    image.save(generate_thumbnail_url(old_url))
