from rest_framework.test import APITestCase
from rest_framework import status


class BrowseViewTestCase(APITestCase):
    def test_get_browse(self):
        response = self.client.get("/browse/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
