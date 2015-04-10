from django.db import models
from neumeeditor.models.name import Name
from neumeeditor.models.style import Style
from neumeeditor.models.fields.short_code_field import ShortCodeField
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Glyph(models.Model):
    class Meta:
        app_label = "neumeeditor"
        # ordering = ['name']

    style = models.ForeignKey(Style, blank=True, null=True)
    short_code = ShortCodeField(max_length=128, blank=False, null=False,
                                unique=False)
    comments = models.TextField(blank=True, null=False)

    def __unicode__(self):
        output = u"{0} : [".format(self.short_code)
        name_count = self.name_set.count()
        index = 0
        for name in self.name_set.all():
            output += u"{0}".format(name.string)
            index += 1
            if index < name_count:
                output += u", "
        return output + "]"


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
