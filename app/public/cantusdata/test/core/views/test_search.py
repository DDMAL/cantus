from rest_framework.test import APITransactionTestCase
from rest_framework import status
from cantusdata.models import Chant, Folio, Manuscript

# Refer to http://www.django-rest-framework.org/api-guide/testing


class MainViewTestCase(APITransactionTestCase):
    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get(self):
        response = self.client.get("/search/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_results(self):
        response = self.client.get("/search/", {"q": "*:*"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_format_override_is_not_a_filter(self):
        response = self.client.get("/search/", {"q": "*:*", "format": "json"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Alone, it is still an empty search.
        response = self.client.get("/search/", {"format": "json"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["numFound"], 0)

    def test_filters_without_a_query(self):
        response = self.client.get("/search/", {"feast": "Nativitas"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_malformed_paging_is_a_bad_request(self):
        for params in ({"q": "*:*", "start": "abc"}, {"q": "*:*", "rows": "-1"}):
            with self.subTest(params=params):
                response = self.client.get("/search/", params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_query_cannot_lift_the_visibility_filter(self):
        Manuscript.objects.create(id=9101, name="Shown", public=True)
        Manuscript.objects.create(id=9102, name="Hidden", public=False)

        def found(query):
            response = self.client.get("/search/", {"q": query, "format": "json"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            return response.json()["numFound"]

        self.assertEqual(found("type:cantusdata_manuscript AND item_id:9101"), 1)
        self.assertEqual(found("type:cantusdata_manuscript AND item_id:9102"), 0)
        # Local params make Solr ignore whatever follows them in q, which is
        # where the visibility filter used to be.
        self.assertEqual(
            found("{!lucene v='type:cantusdata_manuscript AND item_id:9102'}"), 0
        )

    def tearDown(self):
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Manuscript.objects.all().delete()
