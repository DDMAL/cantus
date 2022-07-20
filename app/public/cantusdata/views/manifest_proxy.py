from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from django.http import Http404, JsonResponse
from cantusdata.helpers.postprocess_iiif import iiif_fn
import requests
import json


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
        postprocessing = iiif_fn.get(manifest_url, lambda x: x)
        format_ = kwargs.get("format", None)
        if format_:
            manifest_url += f".{format_}"
        try:
            return JsonResponse(
                postprocessing(json.loads(requests.get(manifest_url).text)),
            )
        except requests.exceptions.RequestException as e:
            raise Http404("Could not retrieve manifest from given url")
