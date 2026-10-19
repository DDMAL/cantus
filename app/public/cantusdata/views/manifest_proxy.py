from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from django.http import Http404, JsonResponse
from cantusdata.helpers.postprocess_iiif import iiif_fn, iiif_default_fns
from cantusdata.metrics.definitions import VIEWER_MANIFEST_LOADS
from cantusdata.metrics.labels import public_manuscripts
from cantusdata.metrics.tracking import outcome_of, track_external
import re
import requests
import json

# (connect, read) seconds. Library servers can be slow, but a hung one must not
# hold a gunicorn worker for the full 600s request timeout.
MANIFEST_TIMEOUT = (5, 30)


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
        manuscript_id = public_manuscripts.id_for_manifest(manifest_url)
        format_ = kwargs.get("format", None)
        if format_:
            manifest_url += f".{format_}"
        outcome = "error"
        try:
            with track_external("manifest_proxy", manifest_url) as tracked:
                response = requests.get(manifest_url, timeout=MANIFEST_TIMEOUT)
                if not response.ok:
                    tracked.outcome = "error"
            manifest_data = json.loads(response.text)
            manifest_data = postprocessing(manifest_data)
            for fn in iiif_default_fns:
                manifest_data = fn(manifest_data)
            outcome = "success"
            return JsonResponse(manifest_data)
        except requests.exceptions.RequestException as e:
            outcome = outcome_of(e)
            raise Http404("Could not retrieve manifest from given url")
        finally:
            VIEWER_MANIFEST_LOADS.labels(manuscript_id, outcome).inc()
