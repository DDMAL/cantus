from django.db import models
from neumeeditor.models.style import Style


class Glyph(models.Model):
    class Meta:
        app_label = "neumeeditor"
        # ordering = ['name']

    # names = models.ManyToOneRel("neumeeditor.Name", related_name="names")
    style = models.ForeignKey(Style)
    image = None

    # def __unicode__(self):e
    #     return u"{0}".format(self.names)
