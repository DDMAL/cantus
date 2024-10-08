"""
Functions for IIIF API boilerplate.
"""


def construct_image_api_url(image_uri: str, **kwargs: str | int) -> str:
    """
    Construct a IIIF image API request URL from an Image URI and
    a set of apotion IIIF Image API parameters. Works with the Image
    API v2 and v3.

    Required parameters:
    - image_uri: The URI of the image to request.

    Optional parameters (see API docs, eg. https://iiif.io/api/image/2.1/):
    - region: The region of the image to request. Region should be a string
    that conforms to the IIIF Image API specification (see link above).
    - size: The size of the image to request.
    - rotation: The rotation of the image to request.
    - quality: The quality of the image to request.
    - format: The format of the image to request.


    Returns:
        The constructed IIIF image API request URL.
    """
    region = kwargs.get("region", "full")  # Default to full image
    size = kwargs.get("size", "pct:50")  # Default to 50% of the original size
    rotation = kwargs.get("rotation", "0")  # Default to no rotation
    quality = kwargs.get("quality", "default")  # Default to default quality
    img_format = kwargs.get("format", "jpg")  # Default to JPEG format
    return f"{image_uri}/{region}/{size}/{rotation}/{quality}.{img_format}"
