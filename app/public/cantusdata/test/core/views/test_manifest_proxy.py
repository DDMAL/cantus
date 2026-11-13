import json
import socket
from typing import Optional
from unittest.mock import patch

import requests
from django.test import TestCase

from cantusdata.helpers import manifests
from cantusdata.helpers.manifests import normalize_manifest_url
from cantusdata.models import Manuscript

PUBLIC_IP = "93.184.216.34"
HOSTS = {
    "iiif.example-library.org": PUBLIC_IP,
    "cdn.example-library.org": "93.184.216.35",
    "gallica.example.org": "93.184.216.36",
    "internal.example": "10.43.0.10",
    "multicast.example": "224.0.0.1",
    "nat64.example": "64:ff9b::7f00:1",
}
MANIFEST = {"@id": "manifest", "sequences": []}
_real_getaddrinfo = socket.getaddrinfo


def fake_getaddrinfo(host, port, *args, **kwargs):  # type: ignore[no-untyped-def]
    # The patch replaces socket.getaddrinfo for everyone, including the Solr
    # sync that saving a manuscript triggers: resolve other hosts for real.
    if host not in HOSTS:
        return _real_getaddrinfo(host, port, *args, **kwargs)
    address = HOSTS[host]
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))]


def response(
    status: int = 200, body: bytes = b"", location: Optional[str] = None
) -> requests.Response:
    fake = requests.Response()
    fake.status_code = status
    fake._content = body  # pylint: disable=protected-access
    fake._content_consumed = True  # pylint: disable=protected-access
    if location:
        fake.headers["Location"] = location
    return fake


def manifest_response() -> requests.Response:
    return response(body=json.dumps(MANIFEST).encode())


@patch("cantusdata.helpers.manifests.socket.getaddrinfo", fake_getaddrinfo)
class ManifestProxyTestCase(TestCase):
    STORED = "https://iiif.example-library.org/ms/1/manifest.json"

    @classmethod
    def setUpTestData(cls) -> None:
        Manuscript.objects.create(
            id=1, name="One", public=True, manifest_url=cls.STORED
        )

    def proxy(self, url: str, **query: str):  # type: ignore[no-untyped-def]
        return self.client.get(f"/manifest-proxy/{url}/", query)

    def test_a_url_that_is_no_manuscripts_manifest_is_never_fetched(self) -> None:
        with patch.object(requests.Session, "get") as get:
            response_ = self.proxy("http://solr:8983/solr/cantus_ultimus_1/select")
        self.assertEqual(response_.status_code, 404)
        get.assert_not_called()

    def test_the_stored_url_is_fetched_however_the_request_spells_it(self) -> None:
        for requested in (
            self.STORED,
            "http://iiif.example-library.org/ms/1/manifest.json",
            # What Traefik leaves of the scheme's slashes.
            "https:/iiif.example-library.org/ms/1/manifest.json",
        ):
            with self.subTest(requested=requested):
                with patch.object(
                    requests.Session, "get", return_value=manifest_response()
                ) as get:
                    response_ = self.proxy(requested)
                self.assertEqual(response_.status_code, 200)
                self.assertEqual(response_.json()["@id"], "manifest")
                self.assertEqual(get.call_args.args[0], self.STORED)

    def test_stored_whitespace_and_query_strings_are_handled(self) -> None:
        stored = (
            "https://gallica.example.org/iiif/ark:/12148/b1/manifest.json"
            "?iiif-content=https://gallica.example.org/iiif/ark:/12148/b1"
        )
        Manuscript.objects.create(id=2, name="Two", manifest_url=stored + "  ")
        with patch.object(
            requests.Session, "get", return_value=manifest_response()
        ) as get:
            response_ = self.proxy(
                "https://gallica.example.org/iiif/ark:/12148/b1/manifest.json",
                **{"iiif-content": "https://gallica.example.org/iiif/ark:/12148/b1"},
            )
        self.assertEqual(response_.status_code, 200)
        self.assertEqual(get.call_args.args[0], stored)

    def test_an_ambiguous_request_is_refused(self) -> None:
        Manuscript.objects.create(
            id=3, name="Three", manifest_url="https://cdn.example-library.org/m"
        )
        Manuscript.objects.create(
            id=4, name="Four", manifest_url="http://cdn.example-library.org/m"
        )
        with patch.object(requests.Session, "get") as get:
            self.assertEqual(
                self.proxy("https://cdn.example-library.org/m").status_code, 404
            )
        get.assert_not_called()

    def test_redirects_into_private_or_special_addresses_are_not_followed(
        self,
    ) -> None:
        for target in (
            "http://internal.example/secret",
            "http://multicast.example/x",
            "http://nat64.example/x",
            # A port other than the scheme's or the stored URL's.
            "https://iiif.example-library.org:8443/x",
            "https://user:secret@iiif.example-library.org/x",
            "file:///etc/passwd",
        ):
            with self.subTest(target=target):
                with patch.object(
                    requests.Session,
                    "get",
                    side_effect=[response(302, location=target), manifest_response()],
                ) as get:
                    self.assertEqual(self.proxy(self.STORED).status_code, 404)
                self.assertEqual(get.call_count, 1)

    def test_redirects_between_public_hosts_are_followed(self) -> None:
        with patch.object(
            requests.Session,
            "get",
            side_effect=[
                response(301, location="https://cdn.example-library.org/m.json"),
                manifest_response(),
            ],
        ) as get:
            response_ = self.proxy(self.STORED)
        self.assertEqual(response_.status_code, 200)
        self.assertEqual(
            get.call_args.args[0], "https://cdn.example-library.org/m.json"
        )

    def test_every_hop_announces_cantus_ultimus(self) -> None:
        with patch.object(
            requests.Session,
            "get",
            side_effect=[
                response(301, location="https://cdn.example-library.org/m.json"),
                manifest_response(),
            ],
        ) as get:
            self.assertEqual(self.proxy(self.STORED).status_code, 200)
        self.assertEqual(
            [call.kwargs["headers"]["User-Agent"] for call in get.call_args_list],
            [manifests.USER_AGENT] * 2,
        )

    def test_redirect_loops_are_cut_off(self) -> None:
        loop = response(302, location=self.STORED)
        with patch.object(requests.Session, "get", return_value=loop) as get:
            self.assertEqual(self.proxy(self.STORED).status_code, 404)
        self.assertEqual(get.call_count, manifests.MAX_REDIRECTS + 1)

    def test_a_stored_url_on_a_private_address_is_refused(self) -> None:
        Manuscript.objects.create(
            id=5, name="Five", manifest_url="http://internal.example/manifest"
        )
        with patch.object(requests.Session, "get") as get:
            self.assertEqual(
                self.proxy("http://internal.example/manifest").status_code, 404
            )
        get.assert_not_called()

    def test_bad_upstream_answers_are_a_bad_gateway(self) -> None:
        for upstream in (
            response(body=b"<html>Not JSON</html>"),
            response(status=500, body=b"{}"),
        ):
            with self.subTest(status=upstream.status_code):
                with patch.object(requests.Session, "get", return_value=upstream):
                    self.assertEqual(self.proxy(self.STORED).status_code, 502)

    def test_oversized_manifests_are_not_read_whole(self) -> None:
        with patch.object(manifests, "MAX_MANIFEST_BYTES", 10):
            with patch.object(
                requests.Session, "get", return_value=manifest_response()
            ):
                self.assertEqual(self.proxy(self.STORED).status_code, 502)

    def test_proxies_from_the_environment_are_ignored(self) -> None:
        seen = []

        def get(session, url, **kwargs):  # type: ignore[no-untyped-def]
            seen.append(session.trust_env)
            return manifest_response()

        with patch.object(requests.Session, "get", get):
            self.proxy(self.STORED)
        self.assertEqual(seen, [False])

    def test_manifest_fixes_apply_by_normalized_url(self) -> None:
        def mark(data):  # type: ignore[no-untyped-def]
            data["fixed"] = True
            return data

        with patch.dict(
            "cantusdata.helpers.postprocess_iiif._iiif_fn_by_url",
            {
                normalize_manifest_url(
                    "http://iiif.example-library.org/ms/1/manifest.json"
                ): mark
            },
        ):
            with patch.object(
                requests.Session, "get", return_value=manifest_response()
            ):
                response_ = self.proxy(self.STORED)
        self.assertTrue(response_.json()["fixed"])


class NormalizeManifestUrlTestCase(TestCase):
    def test_spellings_of_one_manifest_agree(self) -> None:
        canonical = normalize_manifest_url("https://a.example/x/manifest.json")
        for spelling in (
            "http://a.example/x/manifest.json",
            "https:/a.example/x/manifest.json",
            "https://a.example//x/manifest.json/",
            "  https://a.example/x/manifest.json  ",
            "https://a.example/x%2Fmanifest.json",
        ):
            with self.subTest(spelling=spelling):
                self.assertEqual(normalize_manifest_url(spelling), canonical)

    def test_the_query_is_part_of_the_manifest(self) -> None:
        self.assertNotEqual(
            normalize_manifest_url("https://a.example/m?id=1"),
            normalize_manifest_url("https://a.example/m?id=2"),
        )
