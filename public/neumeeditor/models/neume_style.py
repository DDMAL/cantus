from django.db import models


class NeumeStyle(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['name']

    name = models.CharField(max_length=128, blank=False, null=False)
    manuscripts = models.ManyToManyField("cantusdata.Manuscript",
                                         blank=True, null=True)

    def __unicode__(self):
        return u"{0}".format(self.name)