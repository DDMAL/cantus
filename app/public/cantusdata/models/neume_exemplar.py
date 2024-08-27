from django.db import models
from django.utils.html import format_html
from django.contrib import admin

from cantusdata.models.folio import Folio

ADMIN_IMAGE_HEIGHT = 100


class NeumeExemplar(models.Model):
    """
    Store the coordinates of an exemplary instance of a neume of a particular type

    These are used in OMR search to give examples of the neumes available for some
    manuscript
    """

    class Meta:
        app_label = "cantusdata"
        ordering = ["name"]

    name = models.CharField(max_length=255, blank=False, null=False)
    folio = models.ForeignKey(Folio, on_delete=models.CASCADE)

    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()

    @admin.display(description="Image")
    def admin_image(self) -> str:
        """
        Return HTML to display the page snippet for the exemplar

        NOTE: This is intended for use in the admin interface, not the client
        """
        return format_html(
            "<img src={}/{},{},{},{}/,{}/0/default.jpg alt={}/>",
            self.folio.image_uri,
            self.x_coord,
            self.y_coord,
            self.width,
            self.height,
            ADMIN_IMAGE_HEIGHT,
            self.name,
        )
