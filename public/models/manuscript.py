from django.db import models


class Manuscript(models.Model):
    """
        A Manuscript is the top-level model, 
        Pages, Chants, Feasts and Concordances belong to a Manuscript
        (some may be shared among different manuscripts?)
    """
    class Meta:
        app_label = "cantusdata"

    name = models.CharField(max_length=255, blank=True, null=True)
    siglum = models.CharField(max_length=255, blank=True, null=True)
    #reduced max_length, should be safe
    date = models.CharField(max_length=50, blank=True, null=True)
    provenance = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return u"{0}".format(self.siglum)

# maybe a function to get tht total number of chants in a manuscript

#    @property
#    def chant_count(self):
#        for p in self.pages:
#            for c in p.getChants