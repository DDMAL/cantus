"""
Module containing helper functions for generating fake objects
for testing purposes.
"""

import random
from typing import Optional
from cantusdata.models import Folio, NeumeExemplar
from cantusdata.helpers.neume_helpers import NEUME_NAMES
from cantusdata.models.neume_exemplar import EXEMPLAR_IMAGE_SIDE_LENGTH


def create_fake_neume_exemplar(
    folio: Folio,
    name: Optional[str] = None,
    x_coord: Optional[int] = None,
    y_coord: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> NeumeExemplar:
    if name is None:
        name = random.choice(NEUME_NAMES)
    if folio is None:
        raise ValueError("Folio must be provided")
    # Coordinates and dimensions are optional
    # and are set randomly to some generally reasonable values
    if x_coord is None:
        x_coord = random.randint(0, 2100)
    if y_coord is None:
        y_coord = random.randint(0, 2100)
    if width is None:
        width = EXEMPLAR_IMAGE_SIDE_LENGTH
    if height is None:
        height = EXEMPLAR_IMAGE_SIDE_LENGTH
    return NeumeExemplar.objects.create(
        name=name,
        folio=folio,
        x_coord=x_coord,
        y_coord=y_coord,
        width=width,
        height=height,
    )
