from rest_framework.test import APITestCase
from rest_framework import status


class ChantViewTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get_pnames(self):
        # We pass the GET arguments as a dictionary
        response = self.client.get("/notation-search/",
                                   {"q": "edcdeg", "type": "pnames",
                                    "manuscript": "cdn-hsmu-m2149l4"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = '{"numFound": 1, "results": [{"y": 3398.0,' \
                            ' "p": "014r", "x": 880.0, "w": 1351.0,' \
                            ' "h": 222.0}]}'
        self.assertJSONEqual(response.content, expected_response)

    def test_get_neumes(self):
        # We pass the GET arguments as a dictionary
        response = self.client.get("/notation-search/",
                                   {"q": "virga virga clivis torculus"
                                         " punctum clivis",
                                    "type": "neumes",
                                    "manuscript": "cdn-hsmu-m2149l4"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = '{"numFound": 2, "results": [{"y": 1863.0,' \
                            '"p": "015r", "x": 2554.0, "w": 746.0,' \
                            ' "h": 186.0}, {"y": 2260.0, "p": "015r",' \
                            ' "x": 809.0, "w": 76.0, "h": 98.0}]}'
        self.assertJSONEqual(response.content, expected_response)
