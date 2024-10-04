from rest_framework.test import APITestCase
from django.core.management import call_command
from django.urls import reverse
from django.conf import settings

from cantusdata.views.search_notation import SearchNotationView, NotationSearchException
from cantusdata.models import Manuscript, Folio


class TestSearchNotationView(APITestCase):
    search_notation_view = SearchNotationView()

    @classmethod
    def setUpTestData(cls) -> None:
        """
        In order for the index_manuscript_mei command
        to run successfully, we need to create a Manuscript
        and two Folio objects for the two folios for which
        we have test data.
        """
        source = Manuscript.objects.create(
            id=123723, name="Test Manuscript", siglum="TEST"
        )
        Folio.objects.create(
            manuscript=source,
            number="001r",
            image_uri="test_001r.jpg",
        )
        Folio.objects.create(
            manuscript=source,
            number="001v",
            image_uri="test_001r.jpg",
        )

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

    def test_create_query_string(self) -> None:
        with self.subTest("Test invalid query"):
            with self.assertRaises(NotationSearchException):
                self.search_notation_view.create_query_string(
                    "a_b_q", q_type="pitch_names"
                )
        with self.subTest("Test valid query"):
            query = "u   d U r  "
            query_type = "contour"
            query_string = self.search_notation_view.create_query_string(
                query, query_type
            )
            expected_query_string = "contour:u_d_u_r"
            self.assertEqual(query_string, expected_query_string)
        # We add a separate subtest for a "pitch_names_transposed" query since it
        # has a slightly different logic (we get transpositions and chain them
        # together with ORs).
        with self.subTest("Test pitch_names_transposed query"):
            query = "c d e"
            query_type = "pitch_names_transposed"
            query_string = self.search_notation_view.create_query_string(
                query, query_type
            )
            expected_query_string = "pitch_names:(c_d_e OR d_e_f OR e_f_g OR f_g_a OR g_a_b OR a_b_c OR b_c_d)"
            self.assertEqual(query_string, expected_query_string)
        # An intervals query translates interval directions before joining them
        # with underscores.
        with self.subTest("Test intervals query"):
            query = "u2 d3 r u12"
            query_type = "intervals"
            query_string = self.search_notation_view.create_query_string(
                query, query_type
            )
            expected_query_string = "intervals:2_-3_1_12"
            self.assertEqual(query_string, expected_query_string)

    def test_do_query(self) -> None:
        with self.subTest("Test fields returned"):
            # Test that, in general, the fields returned are as expected
            expected_results_fields = [
                "boxes",
                "contour",
                "semitones",
                "pnames",
            ]
            results, _ = self.search_notation_view.do_query(
                123723, "contour:u d u", 100, 0
            )
            results_fields = list(results[0].keys())
            self.assertTrue(set(expected_results_fields).issubset(results_fields))
            # Test a case where we know that neume names are returned and ensure
            # that the "neumes" field is present in the results
            results_neume_names, _ = self.search_notation_view.do_query(
                123723, "neume_names:punctum", 100, 0
            )
            results_neume_names_fields = list(results_neume_names[0].keys())
            expected_results_fields.append("neumes")
            self.assertTrue(
                set(expected_results_fields).issubset(results_neume_names_fields)
            )
        with self.subTest("Test rows and start parameters"):
            results_rows_100_start_0, _ = self.search_notation_view.do_query(
                123723, "neume_names:punctum", 100, 0
            )
            self.assertEqual(len(results_rows_100_start_0), 100)
            results_rows_10_start_0, _ = self.search_notation_view.do_query(
                123723, "neume_names:punctum", 10, 0
            )
            self.assertEqual(len(results_rows_10_start_0), 10)
            self.assertEqual(results_rows_100_start_0[:10], results_rows_10_start_0)
            results_rows_10_start_10, _ = self.search_notation_view.do_query(
                123723, "neume_names:punctum", 10, 10
            )
            self.assertEqual(len(results_rows_10_start_10), 10)
            self.assertEqual(results_rows_100_start_0[10:20], results_rows_10_start_10)
        with self.subTest("Test manuscript_id parameter"):
            _, num_found_123723 = self.search_notation_view.do_query(
                123723, "neume_names:punctum", 100, 0
            )
            _, num_found_123724 = self.search_notation_view.do_query(
                123724, "neume_names:punctum", 100, 0
            )
            self.assertGreater(num_found_123723, 0)
            self.assertEqual(num_found_123724, 0)

    def test_get(self) -> None:
        url = reverse("search-notation-view")
        with self.subTest("Test missing required parameters"):
            params_no_manuscript: dict[str, str | int] = {
                "q": "u d u",
                "type": "contour",
            }
            response_no_manuscript = self.client.get(url, params_no_manuscript)
            self.assertEqual(response_no_manuscript.status_code, 400)
            params_no_type: dict[str, str | int] = {
                "q": "u d u",
                "manuscript_id": 123723,
            }
            response_no_type = self.client.get(url, params_no_type)
            self.assertEqual(response_no_type.status_code, 400)
            params_no_q: dict[str, str | int] = {
                "type": "contour",
                "manuscript_id": 123723,
            }
            response_no_q = self.client.get(url, params_no_q)
            self.assertEqual(response_no_q.status_code, 400)
        with self.subTest("Test response"):
            params: dict[str, str | int] = {
                "q": "u d u",
                "type": "contour",
                "manuscript_id": 123723,
            }
            response = self.client.get(url, params)
            self.assertEqual(response.status_code, 200)
            response_data = response.json()
            self.assertIn("results", response_data)
            self.assertIn("numFound", response_data)

    @classmethod
    def tearDownClass(cls) -> None:
        call_command("index_manuscript_mei", "123723", "--flush-index")
        super().tearDownClass()
