from unittest.mock import patch

import requests
from prometheus_client import REGISTRY
from rest_framework import status
from rest_framework.test import APITestCase
from solr import SolrException  # type: ignore[import-untyped]

from cantusdata.models import Manuscript

SOLRPY_POST = "solr.core.Solr._post"
NOTATION_GET = "cantusdata.views.search_notation.requests.get"


def invalid_searches() -> float:
    return sum(
        sample.value
        for metric in REGISTRY.collect()
        if metric.name == "cantus_search_requests"
        for sample in metric.samples
        if sample.name.endswith("_total")
        and sample.labels.get("outcome") == "invalid_query"
    )


class SolrFailureTestCase(APITestCase):
    """Solr being down is a 502 with a JSON detail, never an unhandled 500."""

    @classmethod
    def setUpTestData(cls) -> None:
        Manuscript.objects.create(id=3, name="Three", siglum="THREE", public=True)

    def assert_bad_gateway(self, path: str, **params: str) -> None:
        response = self.client.get(path, {**params, "format": "json"})
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("detail", response.json())

    def test_unreachable_solr_is_a_bad_gateway(self) -> None:
        with patch(SOLRPY_POST, side_effect=ConnectionRefusedError()):
            for path, params in (
                ("/search/", {"q": "kyrie"}),
                ("/chant-set/manuscript/3/", {}),
                ("/folio-set/manuscript/3/", {}),
            ):
                with self.subTest(path=path):
                    self.assert_bad_gateway(path, **params)
        with patch(NOTATION_GET, side_effect=requests.ConnectionError("refused")):
            self.assert_bad_gateway(
                "/notation-search/", q="u d u", type="contour", manuscript_id="3"
            )

    def test_a_solr_server_error_is_a_bad_gateway(self) -> None:
        with patch(SOLRPY_POST, side_effect=SolrException(500, "Server Error")):
            self.assert_bad_gateway("/search/", q="kyrie")

    def test_a_search_solr_cannot_parse_is_a_bad_request(self) -> None:
        before = invalid_searches()
        refused = SolrException(400, "org.apache.solr.search.SyntaxError")
        with patch(SOLRPY_POST, side_effect=refused):
            response = self.client.get("/search/", {"q": '"kyrie', "format": "json"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.json())
        self.assertEqual(invalid_searches(), before + 1)
