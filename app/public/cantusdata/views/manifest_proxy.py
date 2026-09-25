from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from django.http import JsonResponse
from cantusdata.helpers.postprocess_iiif import iiif_fn, iiif_default_fns
import re
import requests

# Some libraries reject the default python-requests User-Agent: Gallica answers
# "403 Access Interdit" to it, which broke both F-Pn manuscripts (see #937).
MANIFEST_REQUEST_HEADERS = {
    "User-Agent": "CantusUltimus/1.0 (+https://cantus.simssa.ca)",
}

# Wait 5 seconds for the connection and 30 seconds for the body. These requests
# used to have no timeout at all, so a library that stopped responding would
# keep the gunicorn workers busy with a 600 second timeout.
MANIFEST_REQUEST_TIMEOUT = (5, 30)


class ManifestProxyView(APIView):
    """
    This View does the simple task of retrieving a IIIF manifest
    from a url and returning it as it is. The reason why the
    manifest is not directly fetched from the source is that this
    method avoids cross domain mixed content errors. A lot of the
    digital libraries don't support https and browsers thus block
    the retrieval of JSON files from them, if serving from https.
    """

    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        manifest_url = kwargs["manifest_url"]
        # Traefik collapses https:// → https:/ in paths; restore only if actually missing
        manifest_url = re.sub(r"^(https?:/)(?!/)", r"\1/", manifest_url)
        postprocessing = iiif_fn.get(manifest_url, lambda x: x)
        format_ = kwargs.get("format", None)
        if format_:
            manifest_url += f".{format_}"

        try:
            response = requests.get(
                manifest_url,
                headers=MANIFEST_REQUEST_HEADERS,
                timeout=MANIFEST_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            manifest_data = response.json()
            if not isinstance(manifest_data, dict):
                raise ValueError("the manifest is not a JSON object")
        except (requests.exceptions.RequestException, ValueError):
            # A response that is not JSON ends up here too, because requests
            # raises its own JSONDecodeError, which is also a RequestException.
            # So does JSON that parses but is not a manifest at all.
            return JsonResponse(
                {"error": "Could not retrieve manifest from given url"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        manifest_data = postprocessing(manifest_data)
        for fn in iiif_default_fns:
            manifest_data = fn(manifest_data)
        return JsonResponse(manifest_data)
