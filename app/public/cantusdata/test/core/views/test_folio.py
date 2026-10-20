from rest_framework.test import APITransactionTestCase
from rest_framework import status

from cantusdata.models import Folio, Chant, Manuscript

# Refer to http://www.django-rest-framework.org/api-guide/testing


class FolioViewTestCase(APITransactionTestCase):
    fixtures = ["1_users", "2_initial_data"]

    def setUp(self):
        self.client.login(username="ahankins", password="hahaha")

    def test_get_list(self):
        response = self.client.get("/folios/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], Folio.objects.count())

    def test_lookup_is_a_plain_list(self):
        # The viewer reads response[0] (DivaView.js), so no pagination here.
        folio = Folio.objects.get(number="123")
        response = self.client.get(
            "/folios/", {"number": "123", "manuscript": folio.manuscript_id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["number"], "123")

    def test_lookup_input_cannot_break_the_query(self):
        # `(` alone is an invalid database regex; a non-numeric id is no id.
        for params in (
            {"number": "(", "manuscript": "3"},
            {"number": "1", "manuscript": "abc"},
        ):
            with self.subTest(params=params):
                response = self.client.get("/folios/", params)
                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
