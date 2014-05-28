from rest_framework.test import APITestCase
from rest_framework import status

from cantusdata.models import Concordance, Chant, Folio, Manuscript
# Refer to http://www.django-rest-framework.org/api-guide/testing


class ConcordanceViewTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get_list(self):
        response = self.client.get("/concordances/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_detail(self):
        # Grab the first manuscript that exists
        concordance = Concordance.objects.get(letter_code="A")
        if not concordance:
            self.fail("No concordances loading!")
        response = self.client.get("/concordance/{0}/".format(concordance.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_nonexistent_detail(self):
        response = self.client.get("/concordance/2f63f986449349769d7a313e0fc6edb3/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def tearDown(self):
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Concordance.objects.all().delete()
        Manuscript.objects.all().delete()
