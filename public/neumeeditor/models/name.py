from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


class Name(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['string']

    string = models.CharField(max_length=128, blank=False, null=False,
                              unique=True)
    glyph = models.ForeignKey("neumeeditor.Glyph", null=True)

    def __unicode__(self):
        return u"{0}".format(self.string)


@receiver(pre_save, sender=Name)
def strip_whitespace(sender, instance, **kwargs):
    # Strip out whitespace
    print instance.string
    instance.string = instance.string.strip()
