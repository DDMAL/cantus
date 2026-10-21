from django.test import TestCase

from cantusdata.metrics.inventory import InventoryCollector
from cantusdata.models import Chant, Folio, Manuscript, MEISubmission
from cantusdata.models.mei_submission import SubmissionStatus


class InventoryCollectorTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.live = Manuscript.objects.create(
            id=801,
            name="Live",
            siglum="LIVE-1",
            public=True,
            chants_loaded=True,
            is_mapped="MAPPED",
        )
        # A bare CANTUS Database source: counted, but given no series of its own.
        Manuscript.objects.create(id=802, name="Bare", siglum="BARE-1")
        mapped = Folio.objects.create(
            number="001r", image_uri="https://iiif.example/001r", manuscript=cls.live
        )
        Folio.objects.create(number="001v", image_uri="", manuscript=cls.live)
        Chant.objects.create(
            manuscript=cls.live, folio=mapped, sequence=1, volpiano="1---g---h"
        )
        Chant.objects.create(manuscript=cls.live, folio=mapped, sequence=2)
        MEISubmission.objects.create(
            manuscript=cls.live,
            folio=mapped,
            folio_number="001r",
            mei="<mei/>",
            submitter="asadra",
        )

    def collect(self) -> dict[tuple[str, frozenset[tuple[str, str]]], float]:
        return {
            (s.name, frozenset(s.labels.items())): s.value
            for family in InventoryCollector().collect()
            for s in family.samples
        }

    def test_collection_state(self) -> None:
        samples = self.collect()

        # `metric`, not `name`: cantus_manuscript_info has a label called name.
        def value(metric: str, **labels: str) -> float:
            return samples[(metric, frozenset(labels.items()))]

        ms = str(self.live.pk)
        self.assertEqual(
            value(
                "cantus_manuscripts",
                public="true",
                chants_loaded="true",
                mapping_status="MAPPED",
            ),
            1,
        )
        self.assertEqual(
            value(
                "cantus_manuscript_info",
                manuscript_id=ms,
                siglum="LIVE-1",
                name="Live",
                public="true",
            ),
            1,
        )
        self.assertNotIn(
            "802",
            {
                dict(labels).get("manuscript_id")
                for (name, labels) in samples
                if name == "cantus_manuscript_info"
            },
        )
        self.assertEqual(value("cantus_folios", manuscript_id=ms), 2)
        self.assertEqual(value("cantus_folios_with_image", manuscript_id=ms), 1)
        self.assertEqual(value("cantus_chants", manuscript_id=ms), 2)
        self.assertEqual(value("cantus_chants_with_volpiano", manuscript_id=ms), 1)
        self.assertEqual(
            value("cantus_mei_submissions", status=SubmissionStatus.PENDING), 1
        )
        self.assertEqual(
            value("cantus_mei_submissions", status=SubmissionStatus.REFUSED), 0
        )
        self.assertGreaterEqual(value("cantus_mei_oldest_pending_age_seconds"), 0)
        self.assertEqual(value("cantus_mei_oldest_publishing_age_seconds"), 0)
        self.assertEqual(value("cantus_db_records", record_type="chant"), 2)
        self.assertEqual(value("cantus_django_unapplied_migrations"), 0)

    def test_chants_with_stale_visibility_are_counted(self) -> None:
        key = (
            "cantus_solr_chant_visibility_mismatch",
            frozenset({("manuscript_id", str(self.live.pk))}),
        )
        self.assertEqual(self.collect()[key], 0)
        # Hidden in the database, still visible in Solr.
        Manuscript.objects.filter(pk=self.live.pk).update(public=False)
        self.assertEqual(self.collect()[key], 2)

    def test_solr_side_is_read_without_errors(self) -> None:
        samples = self.collect()
        # The Solr test core is shared by the whole run, so other tests' records
        # may be there too; the sync signals put at least these.
        self.assertGreaterEqual(
            samples[
                ("cantus_solr_documents", frozenset({("type", "cantusdata_chant")}))
            ],
            2,
        )
        self.assertEqual(
            samples[
                (
                    "cantus_inventory_collect_errors_total",
                    frozenset({("source", "solr")}),
                )
            ],
            0,
        )
        self.assertEqual(
            samples[
                ("cantus_inventory_collect_errors_total", frozenset({("source", "db")}))
            ],
            0,
        )
        # Every tracked manuscript gets a value, 0 when it has no notation indexed.
        self.assertEqual(
            samples[("cantus_solr_omr_ngrams", frozenset({("manuscript_id", "801")}))],
            0,
        )
