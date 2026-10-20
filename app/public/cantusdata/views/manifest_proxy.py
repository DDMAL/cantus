from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from django.http import Http404, JsonResponse
from cantusdata.helpers.manifests import (
    ManifestUnavailable,
    UnsafeManifestURL,
    fetch_manifest,
    find_known_manifest,
)
from cantusdata.helpers.postprocess_iiif import postprocess_manifest
from cantusdata.metrics.definitions import VIEWER_MANIFEST_LOADS
from cantusdata.metrics.labels import OTHER, manuscript_label
from cantusdata.metrics.tracking import track_external
import re
import json


class ManifestProxyView(APIView):
    """
    This View does the simple task of retrieving a IIIF manifest
    from a url and returning it as it is. The reason why the
    manifest is not directly fetched from the source is that this
    method avoids cross domain mixed content errors. A lot of the
    digital libraries don't support https and browsers thus block
    the retrieval of JSON files from them, if serving from https.

    Only manifests stored on a manuscript are fetched: the URL in the request
    just names one (see helpers/manifests.py).
    """

    renderer_classes = (JSONRenderer,)

    def get(self, request, *args, **kwargs):
        requested = kwargs["manifest_url"]
        # Traefik collapses https:// → https:/ in paths; restore only if actually missing
        requested = re.sub(r"^(https?:/)(?!/)", r"\1/", requested)
        format_ = kwargs.get("format", None)
        if format_:
            requested += f".{format_}"
        # A manifest URL's own query arrives as the request's query string.
        query = request.GET.copy()
        query.pop("format", None)
        if query:
            requested += "?" + query.urlencode()

        known = find_known_manifest(requested)
        if known is None:
            VIEWER_MANIFEST_LOADS.labels(OTHER, "rejected").inc()
            raise Http404("Not the manifest of a known manuscript")
        manuscript_id, manifest_url = known

        outcome = "error"
        try:
            with track_external("manifest_proxy", manifest_url):
                body = fetch_manifest(manifest_url)
            manifest_data = postprocess_manifest(manifest_url, json.loads(body))
            outcome = "success"
            return JsonResponse(manifest_data)
        except UnsafeManifestURL:
            outcome = "rejected"
            raise Http404("Could not retrieve manifest from given url")
        except (ManifestUnavailable, ValueError, KeyError, TypeError):
            # Unreachable server, error page instead of JSON (ValueError covers
            # JSONDecodeError and UnicodeError), or a manifest the
            # post-processing does not understand: the upstream's fault.
            return JsonResponse(
                {"detail": "Could not retrieve the manifest."}, status=502
            )
        finally:
            VIEWER_MANIFEST_LOADS.labels(manuscript_label(manuscript_id), outcome).inc()
