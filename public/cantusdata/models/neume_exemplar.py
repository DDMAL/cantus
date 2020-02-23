from django.db import models

from cantusdata.models.folio import Folio


ADMIN_IMAGE_TEMPLATE = ('<img src="{base_url}/{siglum}_{folio}.jp2/'
                        '{x},{y},{w},{h}/,{img_height}/0/default.jpg" alt="{name}" />')
ADMIN_IMAGE_HEIGHT = 100


class NeumeExemplar(models.Model):
    """Store the coordinates of an exemplary instance of a neume of a particular type

    These are used in OMR search to give examples of the neumes available for some
    manuscript
    """
    class Meta:
        app_label = "cantusdata"
        ordering = ['name']

    name = models.CharField(max_length=255, blank=False, null=False)
    folio = models.ForeignKey(Folio)

    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()

    def admin_image(self):
        """Return HTML to display the page snippet for the exemplar

        NOTE: This is intended for use in the admin interface, not the client
        """
        return ADMIN_IMAGE_TEMPLATE.format(
            base_url='https://images.simssa.ca/iiif/image/cdn-hsmu-m2149l4',
            siglum=self.folio.manuscript.siglum_slug,
            folio=self.folio.number,
            x=self.x_coord,
            y=self.y_coord,
            w=self.width,
            h=self.height,
            img_height=ADMIN_IMAGE_HEIGHT,
            name=self.name
        )

    admin_image.allow_tags = True

    def __str__(self):
        return "{} - {}, {} at ({}, {}), {}x{}".format(self.name, self.folio.manuscript.siglum, self.folio.number,
                                                        self.x_coord, self.y_coord, self.width, self.height)
