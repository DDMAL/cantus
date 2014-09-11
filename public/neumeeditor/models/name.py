from django.db import models
from neumeeditor.models.fields.short_code_field import ShortCodeField


class Name(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['string']

    string = models.CharField(max_length=128, blank=False, null=False,
                              unique=True)
    short_code = ShortCodeField(max_length=128, blank=False, null=False,
                                unique=True)
    glyph = models.ForeignKey("neumeeditor.Glyph", null=True)

    def __unicode__(self):
        return u"{0}".format(self.string)
