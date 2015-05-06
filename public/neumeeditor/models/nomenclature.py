from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from neumeeditor.models.name_nomenclature_membership import \
    NameNomenclatureMembership


class Nomenclature(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['nomenclature_name']

    nomenclature_name = models.CharField(max_length=128, blank=False,
                                         null=False, unique=True)

    def __unicode__(self):
        return u"{0}".format(self.nomenclature_name)


@receiver(pre_delete, sender=Nomenclature)
def delete_name_nomenclature_memberships(sender, instance, **kwargs):
    # Delete all NameNomenclatureMemberships for this Nomenclature
    NameNomenclatureMembership.objects.filter(nomenclature=instance).delete()
