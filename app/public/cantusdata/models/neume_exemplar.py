from typing import Any

from django.db import models
from django.utils.html import format_html
from django.contrib import admin

from cantusdata.models.folio import Folio
from cantusdata.helpers.iiif_helpers import construct_image_api_url
from cantusdata.helpers.neume_helpers import NEUME_NAMES

ADMIN_IMAGE_HEIGHT = 100
EXEMPLAR_IMAGE_SIDE_LENGTH = 80


class NeumeExemplar(models.Model):
    """
    Store the coordinates of an exemplary instance of a neume of a particular type

    These are used in OMR search to give examples of the neumes available for some
    manuscript
    """

    class Meta:
        app_label = "cantusdata"
        ordering = ["order"]

    name = models.CharField(max_length=255, blank=False, null=False)
    folio = models.ForeignKey(Folio, on_delete=models.CASCADE)

    x_coord = models.IntegerField()
    y_coord = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    order = models.IntegerField(
        help_text="""A helper field used to order the exemplars.
         See helpers/neume_helpers.py for an explanation of how this is used.""",
        default=1,
    )

    @admin.display(description="Image")
    def admin_image(self) -> str:
        """
        Return HTML to display the page snippet for the exemplar

        NOTE: This is intended for use in the admin interface, not the client
        """
        image_uri = self.folio.image_uri
        # If a neume exemplar has been chosen, the associated folio should have an image,
        # but in case the uri was removed after selection, we should check for it here
        if image_uri:
            image_url = construct_image_api_url(
                image_uri,
                region=f"{self.x_coord},{self.y_coord},{self.width},{self.height}",
                size=f"{ADMIN_IMAGE_HEIGHT},",
            )
            return format_html(
                "<img src={} alt={}/>",
                image_url,
                self.name,
            )
        return ""

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Calculate the "order" field based on the neume name so that the exemplars
        are ordered consistently.
        """
        # Make the value of order the 1-indexed position of the neume in the list of neumes
        self.order = NEUME_NAMES.index(self.name) + 1
        super().save(*args, **kwargs)
