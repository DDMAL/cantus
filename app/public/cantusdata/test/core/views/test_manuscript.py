from rest_framework.test import APITransactionTestCase
from rest_framework import status

from cantusdata.models import Manuscript, Folio, Chant

# Refer to http://www.django-rest-framework.org/api-guide/testing


class ManuscriptViewTestCase(APITransactionTestCase):
    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get_list(self):
        response = self.client.get("/manuscripts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_detail(self):
        # Grab the first manuscript that exists
        manuscript = Manuscript.objects.get(name="MyName")
        if not manuscript:
            self.fail("No manuscripts loading!")
        response = self.client.get("/manuscript/{0}/".format(manuscript.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_nonexistent_detail(self):
        response = self.client.get("/manuscript/2f63f986449349769d7a313e0fc6edb3/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_private_detail(self):
        manuscript = Manuscript.objects.get(name="NumberTwo")
        if not manuscript:
            self.fail("No manuscripts loading!")
        response = self.client.get("/manuscript/{0}/".format(manuscript.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def tearDown(self):
        Chant.objects.all().delete()
        Folio.objects.all().delete()
        Manuscript.objects.all().delete()
