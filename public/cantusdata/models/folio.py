from django.db import models
from cantusdata.models.chant import Chant


class Folio(models.Model):
    """
    A folio is a manuscript page.
    A manuscript has many folios.  A folio has many chants.
    """
    class Meta:
        app_label = "cantusdata"

    number = models.CharField(max_length=50, blank=True, null=True)
    manuscript = models.ForeignKey("Manuscript")

    def __unicode__(self):
        return u"{0} - {1}".format(self.number, self.manuscript)

    @property
    def chant_count(self):
        return len(Chant.objects.filter(folio=self))