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


def normalize_iiif3_service_type(datadict):
    """
    Normalize image service @type to type for IIIF Presentation 3 manifests.

    Some IIIF Presentation 3 manifests use @type (older JSON-LD convention)
    instead of type in image service blocks. Diva checks for service.type
    to determine the image API version, so @type causes it to fall back to
    Image API 1.0, producing incorrect tile URLs.
    """
    context = datadict.get("@context", [])
    is_presentation_3 = (
        isinstance(context, list)
        and "http://iiif.io/api/presentation/3/context.json" in context
    )
    if not is_presentation_3:
        return datadict
    for canvas in datadict.get("items", []):
        for anno_page in canvas.get("items", []):
            for annotation in anno_page.get("items", []):
                body = annotation.get("body", {})
                service = body.get("service", {})
                if isinstance(service, dict) and "@type" in service and "type" not in service:
                    service["type"] = service.pop("@type")
    return datadict


def compose(*fns):
    """Apply multiple postprocessing functions in sequence."""
    def composed(datadict):
        for fn in fns:
            datadict = fn(datadict)
        return datadict
    return composed


iiif_fn = {
    "https://digital.blb-karlsruhe.de/i3f/v20/1253122/manifest": d_ka_aug_lx,
    "https://adore.ugent.be/IIIF/manifests/archive.ugent.be:082FD364-C35A-11DF-A9D6-99EF78F64438": b_gu_hs_bkt_006,
}

iiif_default_fns = [normalize_iiif3_service_type]
