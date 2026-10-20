from django.conf import settings
from django.test import SimpleTestCase, TestCase

from cantusdata.helpers.solr_client import make_solr

from .utils import BROWSER, sample


class MiddlewareTestCase(TestCase):
    def get(self, path: str, **extra: str):  # type: ignore[no-untyped-def]
        return self.client.get(path, HTTP_USER_AGENT=BROWSER, **extra)

    def test_requests_are_counted_by_route_status_and_client(self) -> None:
        labels = dict(
            method="GET", route="manuscript-list", status="200", client="browser"
        )
        timing = dict(method="GET", route="manuscript-list")
        before = sample("cantus_http_requests_total", **labels)
        timed_before = sample("cantus_http_request_duration_seconds_count", **timing)
        queries_before = sample(
            "cantus_http_request_db_queries_count", route="manuscript-list"
        )

        response = self.get("/manuscripts/", HTTP_ACCEPT="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sample("cantus_http_requests_total", **labels), before + 1)
        self.assertEqual(
            sample("cantus_http_request_duration_seconds_count", **timing),
            timed_before + 1,
        )
        self.assertEqual(
            sample("cantus_http_request_db_queries_count", route="manuscript-list"),
            queries_before + 1,
        )
        self.assertEqual(sample("cantus_http_requests_in_progress"), 0)

    def test_unknown_paths_share_one_route_label(self) -> None:
        labels = dict(method="GET", route="unmatched", status="404", client="browser")
        before = sample("cantus_http_requests_total", **labels)
        self.get("/no-such-page-anywhere/")
        self.assertEqual(sample("cantus_http_requests_total", **labels), before + 1)

    def test_admin_routes_collapse_into_one_label(self) -> None:
        labels = dict(method="GET", route="admin", status="200", client="browser")
        before = sample("cantus_http_requests_total", **labels)
        self.get("/admin/login/")
        self.assertEqual(sample("cantus_http_requests_total", **labels), before + 1)

    def test_only_html_renders_count_as_page_loads(self) -> None:
        labels = dict(page="manuscript-list", client="browser")
        before = sample("cantus_page_loads_total", **labels)
        self.get("/manuscripts/", HTTP_ACCEPT="application/json")
        self.assertEqual(sample("cantus_page_loads_total", **labels), before)
        self.get("/manuscripts/", HTTP_ACCEPT="text/html")
        self.assertEqual(sample("cantus_page_loads_total", **labels), before + 1)


class SearchMetricsTestCase(TestCase):
    def search(self, **params: str):  # type: ignore[no-untyped-def]
        return self.client.get(
            "/search/", params, HTTP_ACCEPT="application/json", HTTP_USER_AGENT=BROWSER
        )

    def test_a_first_page_counts_as_a_search(self) -> None:
        labels = dict(
            field="feast", scope="manuscript", outcome="no_hits", client="browser"
        )
        before = sample("cantus_search_requests_total", **labels)
        results_before = sample("cantus_search_results_count", field="feast")

        response = self.search(q='feast_t_hidden:"Nativitas" AND manuscript_id:"5"')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sample("cantus_search_requests_total", **labels), before + 1)
        self.assertEqual(
            sample("cantus_search_results_count", field="feast"), results_before + 1
        )

    def test_later_pages_of_the_same_search_are_not_new_searches(self) -> None:
        labels = dict(field="all", scope="global", outcome="no_hits", client="browser")
        before = sample("cantus_search_requests_total", **labels)
        offsets_before = sample("cantus_search_result_offset_count")

        self.search(q="kyrie", start="20")

        self.assertEqual(sample("cantus_search_requests_total", **labels), before)
        self.assertEqual(
            sample("cantus_search_result_offset_count"), offsets_before + 1
        )

    def test_invariant_pitch_search_is_reported_as_an_invalid_type(self) -> None:
        # The type the client sends for "Pitch (invariant)", which the server
        # does not accept.
        labels = dict(
            type="invalid",
            manuscript_id="other",
            outcome="invalid_query",
            client="browser",
        )
        before = sample("cantus_notation_search_requests_total", **labels)
        response = self.client.get(
            "/notation-search/",
            {"q": "a b c", "type": "pitch_names_invariant", "manuscript_id": "1"},
            HTTP_USER_AGENT=BROWSER,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            sample("cantus_notation_search_requests_total", **labels), before + 1
        )

    def test_a_valid_notation_search_records_its_shape(self) -> None:
        labels = dict(
            type="contour", manuscript_id="other", outcome="no_hits", client="browser"
        )
        before = sample("cantus_notation_search_requests_total", **labels)
        lengths_before = sample(
            "cantus_notation_search_query_length_sum", type="contour"
        )
        response = self.client.get(
            "/notation-search/",
            {"q": "u d r", "type": "contour", "manuscript_id": "1"},
            HTTP_USER_AGENT=BROWSER,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sample("cantus_notation_search_requests_total", **labels), before + 1
        )
        self.assertEqual(
            sample("cantus_notation_search_query_length_sum", type="contour"),
            lengths_before + 3,
        )


class SolrClientTestCase(SimpleTestCase):
    def test_timeout_is_set_on_the_connection_solrpy_actually_uses(self) -> None:
        client = make_solr("unit", timeout=3)
        self.assertEqual(client.conn.timeout, 3)
        self.assertEqual(client.max_retries, 1)
        self.assertEqual(make_solr("unit").conn.timeout, settings.SOLR_TIMEOUT)

    def test_requests_are_measured_by_operation_and_outcome(self) -> None:
        ok_before = sample(
            "cantus_solr_requests_total", operation="unit_ok", outcome="success"
        )
        make_solr("unit_ok").query("*:*", rows=0)
        self.assertEqual(
            sample(
                "cantus_solr_requests_total", operation="unit_ok", outcome="success"
            ),
            ok_before + 1,
        )

        failed_before = sample(
            "cantus_solr_requests_total", operation="unit_down", outcome="error"
        )
        unreachable = make_solr(
            "unit_down", url="http://127.0.0.1:9/solr/none", timeout=1, max_retries=0
        )
        with self.assertRaises(OSError):
            unreachable.query("*:*")
        self.assertEqual(
            sample(
                "cantus_solr_requests_total", operation="unit_down", outcome="error"
            ),
            failed_before + 1,
        )
