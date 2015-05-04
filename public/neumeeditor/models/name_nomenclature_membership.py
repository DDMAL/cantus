from django.db import models


class NameNomenclatureMembership(models.Model):
    """
    A relationship between a name and a nomenclature.
    """
    name = models.ForeignKey('Name')
    nomenclature = models.ForeignKey('Nomenclature')

    @property
    def glyph(self):
        return self.name.glyph.id
