from unittest.mock import Mock, patch

import requests
from rest_framework import status
from rest_framework.test import APITestCase

from cantusdata.views.manifest_proxy import MANIFEST_REQUEST_TIMEOUT

REQUESTS_GET = "cantusdata.views.manifest_proxy.requests.get"
MANIFEST_URL = "https://example.org/iiif/manifest.json"
MANIFEST = {"@id": MANIFEST_URL, "@type": "sc:Manifest"}
URL = f"/manifest-proxy/{MANIFEST_URL}/"


class ManifestProxyViewTestCase(APITestCase):
    def upstream(self) -> Mock:
        """A healthy response from the library whose manifest we are proxying."""
        response = Mock()
        response.raise_for_status.return_value = None
        # A copy per call, because the postprocessors edit the manifest in place.
        response.json.return_value = dict(MANIFEST)
        return response

    # --- fetching the manifest ------------------------------------------

    def test_manifest_is_proxied_with_an_identifying_user_agent(self) -> None:
        """
        Gallica refuses the default python-requests User-Agent, which left both
        F-Pn manuscripts without images until we sent one of our own (#937).
        """
        with patch(REQUESTS_GET) as requests_get:
            requests_get.return_value = self.upstream()
            response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, MANIFEST)
        self.assertEqual(requests_get.call_args.args[0], MANIFEST_URL)
        headers = requests_get.call_args.kwargs["headers"]
        self.assertIn("CantusUltimus", headers["User-Agent"])
        self.assertEqual(
            requests_get.call_args.kwargs["timeout"], MANIFEST_REQUEST_TIMEOUT
        )

    def test_format_suffix_is_restored_before_fetching(self) -> None:
        """
        The viewer asks for /manifest-proxy/<url> with no trailing slash, so DRF
        takes the .json off as a format suffix and the view has to put it back.
        This is the URL shape every real request uses.
        """
        with patch(REQUESTS_GET) as requests_get:
            requests_get.return_value = self.upstream()
            response = self.client.get(f"/manifest-proxy/{MANIFEST_URL}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(requests_get.call_args.args[0], MANIFEST_URL)

    # --- when the library fails us --------------------------------------

    def test_upstream_error_is_reported_as_bad_gateway(self) -> None:
        upstream = self.upstream()
        upstream.raise_for_status.side_effect = requests.exceptions.HTTPError("403")
        with patch(REQUESTS_GET, return_value=upstream):
            response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    def test_unparseable_body_is_reported_as_bad_gateway(self) -> None:
        """
        The case that used to be a 500: an error page parsed as JSON raises
        JSONDecodeError, which is a ValueError and so escaped the handler for
        request failures.
        """
        upstream = self.upstream()
        upstream.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", "Access Denied: 403 Access Interdit", 0
        )
        with patch(REQUESTS_GET, return_value=upstream):
            response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)

    def test_json_that_is_not_an_object_is_reported_as_bad_gateway(self) -> None:
        """
        Some hosts turn a request away with a bare string or list under a JSON
        content type. That parses, so it would otherwise reach the
        postprocessing and fail there instead.
        """
        upstream = self.upstream()
        upstream.json.return_value = ["Access Denied"]
        with patch(REQUESTS_GET, return_value=upstream):
            response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
