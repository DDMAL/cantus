from cantusdata.helpers.solr_result_parsing import remove_all_solr_metadata
from rest_framework.test import APITestCase
from rest_framework import status


class FolioChantSetViewTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get(self):
        response = self.client.get("/chant-set/folio/1/")
        # Test that we get a response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that it's the response we're expecting
        expected_string = '[{"office": "", "sequence": 72, "item_id": "1",' \
                          ' "differentia": "", "marginalia": "",' \
                          ' "cantus_id": "1234",' \
                          ' "folio": "123", "manuscript": "ABC - 456",' \
                          ' "folio_id": 1, "type": "cantusdata_chant",' \
                          ' "manuscript_name_hidden": "geoff",' \
                          ' "incipit": "5678", "volpiano": "",' \
                          ' "genre": "", "manuscript_id": 3, "full_text": "",' \
                          ' "feast": "", "mode": "", "finalis": "",' \
                          ' "position": ""}]'
        # We want to remove the version id and unique id because they're always
        # different.
        self.assertEqual(remove_all_solr_metadata(response.content),
                         expected_string)


class ManuscriptChantSetTestCase(APITestCase):

    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get(self):
        response = self.client.get("/chant-set/manuscript/3/")
        # Test that we get a response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that it's the response we're expecting
        expected_string = '[{"office": "", "sequence": 72, "item_id": "1",' \
                          ' "differentia": "", "marginalia": "",' \
                          ' "cantus_id": "1234",' \
                          ' "folio": "123", "manuscript": "ABC - 456",' \
                          ' "folio_id": 1,' \
                          ' "type": "cantusdata_chant",' \
                          ' "manuscript_name_hidden": "geoff",' \
                          ' "incipit": "5678", "volpiano": "",' \
                          ' "genre": "", "manuscript_id": 3, "full_text": "",' \
                          ' "feast": "", "mode": "", "finalis": "",' \
                          ' "position": ""}]'
        # We want to remove the version id and unique id because they're always
        # different.
        self.assertEqual(remove_all_solr_metadata(response.content),
                         expected_string)

    def test_get_empty_chant(self):
        response = self.client.get("/chant-set/manuscript/3/page-2/")
        # Test that we get a response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Empty response is just square brackets
        self.assertEqual(response.content, "[]")
