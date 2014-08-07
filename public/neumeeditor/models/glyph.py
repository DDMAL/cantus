from django.db import models
from neumeeditor.models.name import Name
from neumeeditor.models.style import Style
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Glyph(models.Model):
    class Meta:
        app_label = "neumeeditor"
        # ordering = ['name']

    style = models.ForeignKey(Style)
    # image = None

    def test(self):
        self.name_set.clear()


@receiver(pre_delete, sender=Glyph)
def pre_glyph_delete(sender, instance, **kwargs):
    """
    When a glyph is deleted, we delete its names, too!

    :param sender:Glyph
    :param instance:
    :param kwargs:
    :return:
    """
    Name.objects.filter(glyph=sender).delete()
