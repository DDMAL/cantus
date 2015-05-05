import hashlib
from django.db import models
from neumeeditor.helpers.storage.media_file_system import media_file_name, \
    MediaFileSystemStorage


class Image(models.Model):
    class Meta:
        app_label = "neumeeditor"

    image_file = models.ImageField(null=True, upload_to=media_file_name,
                                   storage=MediaFileSystemStorage())
    glyph = models.ForeignKey("neumeeditor.Glyph", null=True)
    md5sum = models.CharField(null=True, blank=True, max_length=36)

    def save(self, *args, **kwargs):
        if not self.pk:  # file is new
            md5 = hashlib.md5()
            for chunk in self.image_file.chunks():
                md5.update(chunk)
            self.md5sum = md5.hexdigest()
        super(Image, self).save(*args, **kwargs)