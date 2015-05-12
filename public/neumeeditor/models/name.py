from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from neumeeditor.models.name_nomenclature_membership import \
    NameNomenclatureMembership
from neumeeditor.models.nomenclature import Nomenclature


class Name(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['string']

    string = models.CharField(max_length=128, blank=False, null=False,
                              unique=True)
    glyph = models.ForeignKey("neumeeditor.Glyph", null=True)
    nomenclatures = models.ManyToManyField(Nomenclature, through='NameNomenclatureMembership', blank=True, null=True)

    def __unicode__(self):
        return u"{0}".format(self.string)


@receiver(pre_save, sender=Name)
def strip_whitespace(sender, instance, **kwargs):
    # Strip out whitespace
    instance.string = instance.string.strip()

@receiver(pre_delete, sender=Name)
def delete_name_nomenclature_memberships(sender, instance, **kwargs):
    # Delete all NameNomenclatureMemberships for this name
    NameNomenclatureMembership.objects.filter(name=instance).delete()
