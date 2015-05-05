from django.db import models


class Nomenclature(models.Model):
    class Meta:
        app_label = "neumeeditor"
        ordering = ['nomenclature_name']

    nomenclature_name = models.CharField(max_length=128, blank=False,
                                         null=False, unique=True)

    def __unicode__(self):
        return u"{0}".format(self.nomenclature_name)
