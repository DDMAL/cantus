from rest_framework.test import APITransactionTestCase
from rest_framework import status
from cantusdata.models import Chant, Folio, Manuscript, Concordance

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

    def tearDown(self):
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Concordance.objects.all().delete()
        Manuscript.objects.all().delete()
