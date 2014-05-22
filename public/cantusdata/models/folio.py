from django.db import models
from cantusdata.models.chant import Chant
from django.db.models.signals import post_save
from django.dispatch import receiver


class Folio(models.Model):
    """
    A folio is a manuscript page.
    A manuscript has many folios.  A folio has many chants.
    """
    class Meta:
        app_label = "cantusdata"

    number = models.CharField(max_length=50, blank=True, null=True)
    manuscript = models.ForeignKey("Manuscript")
    chant_count = models.IntegerField(default=0)

    def __unicode__(self):
        return u"{0} - {1}".format(self.number, self.manuscript)


@receiver(post_save, sender=Chant)
def auto_count_chants(sender, instance, **kwargs):
    """
    Compute the number of chants on the folio whenever a chant is saved.
    """
    folio = instance.folio
    folio.chant_count = len(Chant.objects.filter(folio=folio))
    folio.save()