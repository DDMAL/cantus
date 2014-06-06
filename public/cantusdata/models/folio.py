from django.db import models
from cantusdata.models.chant import Chant
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Folio(models.Model):
    """
    A folio is a manuscript page.
    A manuscript has many folios.  A folio has many chants.
    """
    class Meta:
        app_label = "cantusdata"
        ordering = ['number']

    number = models.CharField(max_length=50, blank=True, null=True)
    manuscript = models.ForeignKey("Manuscript")
    chant_count = models.IntegerField(default=0)

    def __unicode__(self):
        return u"{0} - {1}".format(self.number, self.manuscript)


@receiver(post_delete, sender=Chant)
def pre_chant_delete(sender, instance, **kwargs):
    auto_count_chants(instance)


@receiver(post_save, sender=Chant)
def post_chant_delete(sender, instance, **kwargs):
    auto_count_chants(instance)


def auto_count_chants(chant):
    """
    Compute the number of chants on the chant's folio
    """
    folio = chant.folio
    if folio:
        folio.chant_count = len(Chant.objects.filter(folio=folio))
        folio.save()
