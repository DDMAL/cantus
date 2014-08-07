from django.db import models
from neumeeditor.models.neume_style import NeumeStyle


class Glyph(models.Model):
    class Meta:
        app_label = "neumeeditor"
        # ordering = ['name']

    # names = models.ManyToOneRel("neumeeditor.Name", related_name="names")
    style = models.ForeignKey(NeumeStyle)

    # def __unicode__(self):e
    #     return u"{0}".format(self.names)
