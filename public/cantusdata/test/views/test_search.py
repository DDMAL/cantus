from rest_framework.test import APITestCase
from rest_framework import status

# Refer to http://www.django-rest-framework.org/api-guide/testing


class MainViewTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get(self):
        response = self.client.get("/search/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_results(self):
        response = self.client.get("/search/", {'q': '*:*'})
        print response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
