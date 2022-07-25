"""Customizations for certain IIIF manifests that will not work as provided"""
import urllib


def d_ka_aug_lx(datadict):
    """
    Remove additional width/height attributes from the IIIF manifest.

    The width and height attributes provided per folio distort the logic of the
    viewer. We only get sections of the folio instead of the entire folio.
    """
    canvases = datadict["sequences"][0]["canvases"]
    for canvas in canvases:
        images = canvas["images"]
        for image in images:
            resource = image["resource"]
            resource.pop("height")
            resource.pop("width")
    return datadict


def b_gu_hs_bkt_006(datadict):
    """
    Decode encodings from image URLs in the IIIF manifest.

    Colons and backslashes are already encoded in the image ID
    URLs in this manifest. These get re-encoded by the diva viewer,
    so we should pass the decoded URLs to diva.
    """
    canvases = datadict["sequences"][0]["canvases"]
    for canvas in canvases:
        images = canvas["images"]
        resource = images[0]["resource"]
        service = resource["service"]
        service["@id"] = urllib.parse.unquote(service["@id"])
    return datadict


iiif_fn = {
    "https://digital.blb-karlsruhe.de/i3f/v20/1253122/manifest": d_ka_aug_lx,
    "https://adore.ugent.be/IIIF/manifests/archive.ugent.be:082FD364-C35A-11DF-A9D6-99EF78F64438": b_gu_hs_bkt_006,
}
