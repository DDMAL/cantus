from django.db import models


class Image(models.Model):
    class Meta:
        app_label = "neumeeditor"

    image_file = models.ImageField(null=True)
    glyph = models.ForeignKey("neumeeditor.Glyph", null=True)
