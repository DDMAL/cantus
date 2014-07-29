from cantusdata.helpers.solr_result_parsing import remove_all_solr_metadata
from rest_framework.test import APITestCase
from rest_framework import status


class ManuscriptFolioSetViewTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get(self):
        response = self.client.get("/folio-set/manuscript/3/")
        # Test that we get a response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that it's the response we're expecting
        expected_string = '[{"manuscript_id": 3, "number": "123",' \
                          ' "item_id": "1", "type": "cantusdata_folio"}]'
        # We want to remove the version id and unique id because they're always
        # different.
        self.assertEqual(remove_all_solr_metadata(response.content),
                         expected_string)

    def test_get_specific_folio(self):
        response = self.client.get("/folio-set/manuscript/3/123/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_string = '{"manuscript_id": 3, "number": "123",' \
                          ' "item_id": "1", "type": "cantusdata_folio"}'
        # Empty response is just square brackets
        self.assertEqual(remove_all_solr_metadata(response.content),
                         expected_string)

    def test_get_empty_folio(self):
        response = self.client.get("/folio-set/manuscript/3/66666666666/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Empty response is just square brackets
        self.assertEqual(response.content, "[]")
