from unittest.mock import patch

import requests
from rest_framework import status
from rest_framework.test import APITestCase

SOLR_GET = "cantusdata.views.suggestion.solr_get"


class SuggestionViewTestCase(APITestCase):
    def suggest(self, **params: str):  # type: ignore[no-untyped-def]
        return self.client.get("/suggest/", params)

    def test_missing_parameters_are_a_bad_request(self) -> None:
        complete = {"q": "nat", "field": "feast", "manuscript_id": "*"}
        for missing in complete:
            params = {k: v for k, v in complete.items() if k != missing}
            with self.subTest(missing=missing):
                response = self.suggest(**params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(missing, response.json()["detail"])

    def test_malformed_parameters_are_a_bad_request(self) -> None:
        for params in (
            {"q": "nat", "field": "incipit", "manuscript_id": "*"},
            {"q": "nat", "field": "feast", "manuscript_id": "abc"},
            {"q": "nat", "field": "feast", "manuscript_id": "1 OR *:*"},
        ):
            with self.subTest(params=params):
                response = self.suggest(**params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manuscript_ids_as_the_client_sends_them(self) -> None:
        # The client quotes the id inside a manuscript, and sends '*' outside one.
        for manuscript_id in ('"123723"', "123723", "*"):
            with self.subTest(manuscript_id=manuscript_id):
                response = self.suggest(
                    q="nat", field="feast", manuscript_id=manuscript_id
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIsInstance(response.json(), list)

    def test_solr_failures_are_a_bad_gateway(self) -> None:
        failed = requests.Response()
        failed.status_code = 500
        for outcome in (
            {"return_value": failed},
            {"side_effect": requests.ConnectionError("refused")},
        ):
            with self.subTest(outcome=outcome):
                with patch(SOLR_GET, **outcome):
                    response = self.suggest(q="nat", field="feast", manuscript_id="*")
                self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
