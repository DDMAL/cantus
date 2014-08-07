from django.db import models
from neumeeditor.models.neume_style import NeumeStyle


class Glyph(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False, null=False)
    style = models.ForeignKey(NeumeStyle)

    def __unicode__(self):
        return u"{0}".format(self.name)
