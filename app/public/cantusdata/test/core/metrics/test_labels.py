from django.test import RequestFactory, SimpleTestCase, TestCase

from cantusdata.metrics.labels import (
    OTHER,
    classify_client,
    manuscript_label,
    notation_type_label,
    parse_search_query,
    public_manuscripts,
    search_manuscript_id,
    upstream_host_label,
)
from cantusdata.metrics.search_log import normalize_term
from cantusdata.models.manuscript import Manuscript
from cantusdata.views.mei_submission import rejection_reason

from .utils import BROWSER


class ClassifyClientTestCase(SimpleTestCase):
    def classify(self, **meta: str) -> str:
        return classify_client(RequestFactory().get("/", **meta))

    def test_token_authenticated_callers_are_api_clients(self) -> None:
        # Even with a library user agent that would otherwise read as a bot.
        self.assertEqual(
            self.classify(
                HTTP_AUTHORIZATION="Token abc123",
                HTTP_USER_AGENT="python-requests/2.32.3",
            ),
            "api",
        )

    def test_monitoring_is_a_probe_not_a_bot(self) -> None:
        for agent in ("kube-probe/1.30", "Blackbox Exporter/0.25.0"):
            with self.subTest(agent=agent):
                self.assertEqual(self.classify(HTTP_USER_AGENT=agent), "probe")

    def test_crawlers_scripts_and_blank_agents_are_bots(self) -> None:
        for agent in (
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "curl/8.5.0",
            "python-requests/2.32.3",
            "",
        ):
            with self.subTest(agent=agent):
                self.assertEqual(self.classify(HTTP_USER_AGENT=agent), "bot")

    def test_browsers(self) -> None:
        self.assertEqual(self.classify(HTTP_USER_AGENT=BROWSER), "browser")


class SearchLabelTestCase(SimpleTestCase):
    def test_query_fields_and_scope(self) -> None:
        # Queries as SolrQuery.toString builds them.
        cases = {
            "Kyrie eleison": ("all", "global"),
            'feast_t_hidden:"Nativitas Domini"': ("feast", "global"),
            '"Kyrie" AND manuscript_id:"123723"': ("all", "manuscript"),
            'mode_t_hidden:(1 OR 2) AND manuscript_id:"5"': ("mode", "manuscript"),
            'volpiano:"1---g---h"': ("volpiano", "global"),
            'genre_t_hidden:"A" AND office_t_hidden:"M"': ("multi", "global"),
            "anything:goes": (OTHER, "global"),
            # An escaped colon is part of the term, not a field.
            "Deus\\: in adjutorium": ("all", "global"),
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(parse_search_query(query), expected)

    def test_scoped_manuscript_is_read_from_the_query(self) -> None:
        self.assertEqual(search_manuscript_id('x AND manuscript_id:"42"'), "42")
        self.assertIsNone(search_manuscript_id("x"))

    def test_notation_types_outside_the_known_set_are_invalid(self) -> None:
        self.assertEqual(notation_type_label("contour"), "contour")
        # What the client sends for "Pitch (invariant)" (OMRSearchProvider.js).
        self.assertEqual(notation_type_label("pitch_names_invariant"), "invalid")
        self.assertEqual(notation_type_label(None), "invalid")

    def test_logged_terms_drop_the_manuscript_restriction(self) -> None:
        self.assertEqual(
            normalize_term('feast_t_hidden:"Nativitas"  AND manuscript_id:"5"'),
            'feast:"nativitas"',
        )
        self.assertEqual(len(normalize_term("a" * 500)), 200)

    def test_rejection_reasons_are_bounded(self) -> None:
        self.assertEqual(rejection_reason({"folio_number": ["x"]}), "folio_number")
        self.assertEqual(rejection_reason({"mei": ["x"], "comment": ["y"]}), "mei")
        self.assertEqual(rejection_reason({"made_up": ["x"]}), "other")
        self.assertEqual(rejection_reason(["x"]), "other")


class ManuscriptLabelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.public = Manuscript.objects.create(
            id=901,
            name="Public",
            public=True,
            manifest_url="https://iiif.example-library.org/ms/901/manifest.json",
        )
        cls.private = Manuscript.objects.create(
            id=902,
            name="Private",
            public=False,
            manifest_url="https://private.example.org/ms/902/manifest.json",
        )

    def setUp(self) -> None:
        public_manuscripts.reset()

    def test_only_public_manuscripts_get_their_own_label(self) -> None:
        self.assertEqual(manuscript_label(901), "901")
        self.assertEqual(manuscript_label("901"), "901")
        self.assertEqual(manuscript_label(902), OTHER)
        self.assertEqual(manuscript_label(999999), OTHER)

    def test_manifest_urls_map_to_their_manuscript_whatever_the_scheme(self) -> None:
        self.assertEqual(
            public_manuscripts.id_for_manifest(
                "http://iiif.example-library.org/ms/901/manifest.json"
            ),
            "901",
        )
        self.assertEqual(
            public_manuscripts.id_for_manifest("https://elsewhere.org/x.json"), OTHER
        )

    def test_only_known_hosts_become_upstream_labels(self) -> None:
        self.assertEqual(
            upstream_host_label("https://iiif.example-library.org/anything"),
            "iiif.example-library.org",
        )
        self.assertEqual(
            upstream_host_label("https://cantusdatabase.org/json-sources/"),
            "cantusdatabase.org",
        )
        # The manifest proxy fetches whatever it is given: an arbitrary host
        # must not become a new series.
        self.assertEqual(upstream_host_label("http://solr:8983/solr/select"), OTHER)
        self.assertEqual(upstream_host_label("https://private.example.org/x"), OTHER)
