"""Customizations for certain IIIF manifests that will not work as provided"""


def d_ka_aug_lx(datadict):
    """
    Remove additional width/height attributes from the IIIF manifest.

    The width and height attributes provided per folio distort the logic of the
    viewer. We only get sections of the folio instead of the entire folio.
    """
    return datadict


iiif_fn = {
    "https://digital.blb-karlsruhe.de/i3f/v20/1253122/manifest": d_ka_aug_lx
}
