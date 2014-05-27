from rest_framework.test import APITestCase
from rest_framework import status

from cantusdata.models import Folio, Chant, Manuscript
# Refer to http://www.django-rest-framework.org/api-guide/testing


class FolioViewTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get_list(self):
        response = self.client.get("/folios/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_detail(self):
        # Grab the first manuscript that exists
        folio = Folio.objects.get(number="123")
        if not folio:
            self.fail("No folios loading!")
        response = self.client.get("/folio/{0}/".format(folio.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_nonexistent_detail(self):
        response = self.client.get("/chant/2f63f986449349769d7a313e0fc6edb3/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def tearDown(self):
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Manuscript.objects.all().delete()
