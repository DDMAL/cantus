from django.test import TestCase, Client
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, APIClient
from cantusdata.models import Manuscript, Folio, NeumeExemplar
from cantusdata.models.neume_exemplar import EXEMPLAR_IMAGE_SIDE_LENGTH
from cantusdata.views.neume_exemplars import NeumeSetAPIView, PickNeumeExemplarsView
from cantusdata.test.core.fake_generators import create_fake_neume_exemplar


def set_up_neume_exemplar_test_data() -> None:
    """
    Create a Manuscript and two Folio objects for the three folios for which
    we have test MEI data.
    """
    source = Manuscript.objects.create(id=123723, name="Test Manuscript", siglum="TEST")
    Folio.objects.create(
        manuscript=source,
        number="001r",
        image_uri="test_001r.jpg",
    )
    Folio.objects.create(
        manuscript=source,
        number="001v",
        image_uri="test_001v.jpg",
    )
    Folio.objects.create(
        manuscript=source,
        number="999r",
        image_uri="test_999r.jpg",
    )
    # Create a user
    User = get_user_model()
    User.objects.create_user(username="testuser", password="12345", is_staff=True)


class TestNeumeSetView(TestCase):
    neume_set_view = NeumeSetAPIView()

    @classmethod
    def setUpTestData(cls) -> None:
        set_up_neume_exemplar_test_data()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        call_command(
            "index_manuscript_mei",
            "123723",
            "--min-ngram",
            "1",
            "--max-ngram",
            "5",
            "--mei-dir",
            settings.TEST_MEI_FILES_PATH,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def test_fetch_potential_exemplars(self) -> None:
        with self.subTest(neume_name="punctum"):
            potential_exemplars = self.neume_set_view._fetch_potential_exemplars(
                manuscript_id=123723, neume_name="punctum", start=0, rows=10
            )
            self.assertEqual(len(potential_exemplars), 10)
            # There are more than 10 puncta on folio 001r, so all folios for
            # the returned potential exemplars should be 001r
            exemplar_folios_punctum = {
                exemplar["folio"] for exemplar in potential_exemplars
            }
            self.assertEqual(exemplar_folios_punctum, {"001r"})
        with self.subTest(neume_name="compound"):
            # 1 compound neume exists on each of 001r, 001v, and 999r
            potential_exemplars = self.neume_set_view._fetch_potential_exemplars(
                manuscript_id=123723, neume_name="compound", start=0, rows=10
            )
            self.assertEqual(len(potential_exemplars), 3)
            # Exemplars are sorted in folio order
            exemplar_folios = [exemplar["folio"] for exemplar in potential_exemplars]
            self.assertEqual(exemplar_folios, ["001r", "001v", "999r"])
            # Check the image URL for the first exemplar (on 001r)
            ulx1, uly1, width1, height1 = self.neume_set_view.calculate_exemplar_box(
                4520, 2008, 355, 201
            )
            expected_img_url1 = (
                "test_001r.jpg/"
                f"{ulx1},{uly1},{width1},{height1}/{EXEMPLAR_IMAGE_SIDE_LENGTH},"
                "/0/default.jpg"
            )
            self.assertEqual(potential_exemplars[0]["image_url"], expected_img_url1)
            # Check the image URL for the second exemplar (on 001v)
            ulx2, uly2, width2, height2 = self.neume_set_view.calculate_exemplar_box(
                4130, 4769, 402, 188
            )
            expected_img_url2 = (
                "test_001v.jpg/"
                f"{ulx2},{uly2},{width2},{height2}/{EXEMPLAR_IMAGE_SIDE_LENGTH},"
                "/0/default.jpg"
            )
            self.assertEqual(potential_exemplars[1]["image_url"], expected_img_url2)
        with self.subTest(neume_name="porrectus-flexus"):
            # 0 porrectus-flexus neumes exist on these pages
            potential_exemplars = self.neume_set_view._fetch_potential_exemplars(
                manuscript_id=123723, neume_name="porrectus-flexus", start=0, rows=10
            )
            self.assertEqual(len(potential_exemplars), 0)

    def test_get(self) -> None:
        factory = APIRequestFactory()
        with self.subTest("Punctum: first 10 exemplars"):
            request = factory.get(
                reverse("neume-set-view", kwargs={"pk": 123723}),
                {"neume_name": "punctum"},
            )
            response = NeumeSetAPIView.as_view()(
                request, pk=123723, neume_name="punctum"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["neume_name"], "punctum")
            self.assertEqual(response.data["manuscript"], 123723)
            self.assertEqual(response.data["start"], 0)
            self.assertEqual(
                response.data["exemplar_image_side_length"], EXEMPLAR_IMAGE_SIDE_LENGTH
            )
            potential_exemplars = self.neume_set_view._fetch_potential_exemplars(
                manuscript_id=123723, neume_name="punctum", start=0, rows=10
            )
            self.assertEqual(response.data["neume_exemplars"], potential_exemplars)
        with self.subTest("Punctum: exemplars 10 - 15"):
            request = factory.get(
                reverse("neume-set-view", kwargs={"pk": 123723}),
                {"neume_name": "punctum", "start": "10", "rows": "5"},
            )
            response = NeumeSetAPIView.as_view()(request, pk=123723)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["neume_name"], "punctum")
            self.assertEqual(response.data["start"], "10")
            potential_exemplars = self.neume_set_view._fetch_potential_exemplars(
                manuscript_id=123723, neume_name="punctum", start=10, rows=5
            )
            self.assertEqual(response.data["neume_exemplars"], potential_exemplars)
        with self.subTest("No neume name given"):
            request = factory.get(reverse("neume-set-view", kwargs={"pk": 123723}))
            response = NeumeSetAPIView.as_view()(request, pk=123723, neume_name="")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["neume_name"], "")
            # Check that no neume_names has an underscore (i.e. check
            # that we have only returned single-neume exemplars)
            for exemplar in response.data["neume_exemplars"]:
                self.assertNotIn("_", exemplar["neume_name"])


class TestPickNeumeExemplarsView(TestCase):
    pick_neume_exemplars_view = PickNeumeExemplarsView()

    @classmethod
    def setUpTestData(cls) -> None:
        set_up_neume_exemplar_test_data()
        # Create three existing NeumeExemplar objects
        # for manuscript 123723
        folio_001r = Folio.objects.get(manuscript=123723, number="001r")
        folio_001v = Folio.objects.get(manuscript=123723, number="001v")
        create_fake_neume_exemplar(folio_001r, name="punctum")
        create_fake_neume_exemplar(folio_001v, name="compound")
        create_fake_neume_exemplar(folio_001v, name="scandicus")

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        call_command(
            "index_manuscript_mei",
            "123723",
            "--min-ngram",
            "1",
            "--max-ngram",
            "5",
            "--mei-dir",
            settings.TEST_MEI_FILES_PATH,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def test_check_indexed_mei(self) -> None:
        manuscript_123723 = Manuscript.objects.get(id=123723)
        self.assertTrue(
            self.pick_neume_exemplars_view.check_indexed_mei(
                manuscript=manuscript_123723
            )
        )
        # Create an additional manuscript object that won't
        # have any MEI data indexed
        manuscript_123724 = Manuscript.objects.create(
            id=123724, name="Test Manuscript 2", siglum="TEST2"
        )
        self.assertFalse(
            self.pick_neume_exemplars_view.check_indexed_mei(
                manuscript=manuscript_123724
            )
        )

    def test_view(self) -> None:
        client = Client()
        response = client.get(
            reverse("pick-neume-exemplars-view", kwargs={"pk": 123723})
        )
        # The response should be a redirect to the login page
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))  # type: ignore[attr-defined]
        # Log in as a staff member
        client.login(username="testuser", password="12345")
        response = client.get(
            reverse("pick-neume-exemplars-view", kwargs={"pk": 123723})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/pick_neume_exemplars.html")
        with self.subTest("Check context"):
            self.assertEqual(response.context["ngrams_indexed"], True)
            self.assertEqual(response.context["manuscript"].id, 123723)
        with self.subTest(
            "Check that existing neume exemplars populate html form fields"
        ):
            decoded_html = response.content.decode()
            for neume_name, neume_data_dict in response.context["neume_data"].items():
                if neume_data_dict["current_neume_exemplar"] is not None:
                    expected_html_input_elem = (
                        f'<input type="hidden" name="{neume_name}" '
                        f'value="{neume_data_dict["current_neume_exemplar"]}" '
                        'class="neume-exemplar-input" '
                        f'id="{neume_name}-exemplar-input">'
                    )
                    self.assertInHTML(expected_html_input_elem, decoded_html)
                else:
                    expected_html_input_elem = (
                        f'<input type="hidden" name="{neume_name}" '
                        'value="" class="neume-exemplar-input" '
                        f'id="{neume_name}-exemplar-input">'
                    )
                    self.assertInHTML(expected_html_input_elem, decoded_html)

    def test_existing_neume_exemplars(self) -> None:
        manuscript_123723 = Manuscript.objects.get(id=123723)
        existing_exemplar_links = (
            self.pick_neume_exemplars_view.get_existing_exemplar_links(
                manuscript=manuscript_123723
            )
        )
        self.assertEqual(len(existing_exemplar_links), 3)
        self.assertEqual(
            set(existing_exemplar_links.keys()), {"punctum", "compound", "scandicus"}
        )


class TestNeumeExemplarsAPIView(TestCase):
    fake_nes: list[NeumeExemplar] = []

    @classmethod
    def setUpTestData(cls) -> None:
        set_up_neume_exemplar_test_data()
        # Create three existing NeumeExemplar objects
        # for manuscript 123723
        folio_001r = Folio.objects.get(manuscript=123723, number="001r")
        folio_001v = Folio.objects.get(manuscript=123723, number="001v")
        punctum_ne = create_fake_neume_exemplar(folio_001r, name="punctum")
        compound_ne = create_fake_neume_exemplar(folio_001v, name="compound")
        scandicus_ne = create_fake_neume_exemplar(folio_001v, name="scandicus")
        cls.fake_nes = [punctum_ne, compound_ne, scandicus_ne]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        call_command(
            "index_manuscript_mei",
            "123723",
            "--min-ngram",
            "1",
            "--max-ngram",
            "5",
            "--mei-dir",
            settings.TEST_MEI_FILES_PATH,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()

    def test_get(self) -> None:
        client = APIClient()
        response = client.get(reverse("neume-exemplars-view", kwargs={"pk": 123723}))
        self.assertEqual(response.status_code, 200)
        neume_names = {neume_exemplar.name for neume_exemplar in self.fake_nes}
        self.assertEqual(neume_names, {ne["name"] for ne in response.data})

    def test_post(self) -> None:
        client = APIClient()
        with self.subTest("Test that a POST request is refused without authentication"):
            response = client.post(
                reverse("neume-exemplars-view", kwargs={"pk": 123723})
            )
            self.assertEqual(response.status_code, 403)
        with self.subTest("Test that a POST request is accepted with authentication"):
            client.login(username="testuser", password="12345")
            response = client.post(
                reverse("neume-exemplars-view", kwargs={"pk": 123723})
            )
            self.assertEqual(response.status_code, 302)
            expected_redirect_url = reverse(
                "admin:cantusdata_manuscript_change", args=[123723]
            )
            self.assertEqual(response.url, expected_redirect_url)  # type: ignore[attr-defined]
        with self.subTest(
            "Test that the POST request adds/updates the neume exemplars"
        ):
            # Check that three neume exemplars are currently associated with the manuscript
            manuscript_123723 = Manuscript.objects.get(id=123723)
            self.assertEqual(
                NeumeExemplar.objects.filter(
                    folio__manuscript=manuscript_123723
                ).count(),
                3,
            )
            # Create a POST request with some neume exemplar data
            post_data = {
                "punctum": "test_001r.jpg/1,2,3,4/0/0/default.jpg",
                "compound": "test_001r.jpg/2,3,4,5/0/0/default.jpg",
                "scandicus": "test_001r.jpg/3,4,5,6/0/0/default.jpg",
            }
            response = client.post(
                reverse("neume-exemplars-view", kwargs={"pk": 123723}), post_data
            )
            self.assertEqual(response.status_code, 302)
            # Check that the neume exemplars have been updated
            self.assertEqual(
                NeumeExemplar.objects.filter(
                    folio__manuscript=manuscript_123723
                ).count(),
                3,
            )
            for neume_name, _ in post_data.items():
                exemplar = NeumeExemplar.objects.get(name=neume_name)
                self.assertEqual(exemplar.folio.number, "001r")
