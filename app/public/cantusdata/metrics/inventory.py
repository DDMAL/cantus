"""
State of the collection, read from the database and Solr when Prometheus scrapes.

These are the gauges nothing in the request path updates -- how many manuscripts
are live, how complete each one's data is, how long the MEI review queue is,
whether Solr has drifted from the database. They are computed only by the
metrics exporter (`manage.py serve_metrics`), never by the web or task
processes, and cached so that an extra scraper costs no extra queries.
"""

import logging
import threading
import time
from collections import Counter as Tally
from typing import Any, Iterable, Iterator, Optional

from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import Count, Min, Q
from django.utils import timezone
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily, Metric
from prometheus_client.registry import Collector

from cantusdata.helpers.solr_client import solr_get

logger = logging.getLogger(__name__)

CACHE_SECONDS = 60
STATEMENT_TIMEOUT = "10s"
SOLR_TIMEOUT_SECONDS = 5
UNFINISHED_TASK_STATES = ("PENDING", "RECEIVED", "STARTED", "RETRY")


def _bool_label(value: bool) -> str:
    return "true" if value else "false"


def _facet_pairs(facet: list[Any]) -> Iterator[tuple[str, int]]:
    """Solr returns facets as [value, count, value, count, ...]."""
    for i in range(0, len(facet), 2):
        yield str(facet[i]), int(facet[i + 1])


class InventoryCollector(Collector):
    def __init__(self, build_labels: Optional[dict[str, str]] = None) -> None:
        self._lock = threading.Lock()
        self._cached: list[Metric] = []
        self._cached_at: Optional[float] = None
        self._errors: Tally[str] = Tally()
        self._build_labels = build_labels or {}

    def collect(self) -> Iterable[Metric]:
        with self._lock:
            now = time.monotonic()
            if self._cached_at is None or now - self._cached_at >= CACHE_SECONDS:
                self._cached = self._compute()
                self._cached_at = now
            return list(self._cached)

    def _compute(self) -> list[Metric]:
        families: list[Metric] = []
        durations = GaugeMetricFamily(
            "cantus_inventory_collect_duration_seconds",
            "Time taken to read the inventory, by source.",
            labels=["source"],
        )
        try:
            for source, read in (
                ("db", self._db_families),
                ("solr", self._solr_families),
            ):
                start = time.perf_counter()
                try:
                    families.extend(read())
                except Exception:  # pylint: disable=broad-exception-caught
                    # One unreachable source must not hide the other's gauges.
                    logger.exception("Reading the %s inventory failed", source)
                    self._errors[source] += 1
                durations.add_metric([source], time.perf_counter() - start)
        finally:
            # Each scrape is served on a new thread, and Django keeps one
            # connection per thread: close it rather than leak one per scrape.
            # (Inside a transaction -- only ever a test's -- it is not ours.)
            if not connection.in_atomic_block:
                connection.close()
        errors = CounterMetricFamily(
            "cantus_inventory_collect_errors",
            "Inventory reads that failed, by source.",
            labels=["source"],
        )
        for source in ("db", "solr"):
            errors.add_metric([source], self._errors[source])
        families.extend([durations, errors])
        if self._build_labels:
            build = GaugeMetricFamily(
                "cantus_build_info",
                "Always 1; labels identify the running build.",
                labels=list(self._build_labels),
            )
            build.add_metric(list(self._build_labels.values()), 1)
            families.append(build)
        return families

    # Database ----------------------------------------------------------------

    def _db_families(self) -> list[Metric]:
        # Imported here: the collector module is imported before apps are ready.
        from django_celery_results.models import TaskResult

        from cantusdata.models import Chant, Folio, Manuscript, NeumeExemplar
        from cantusdata.models.mei_submission import MEISubmission, SubmissionStatus
        from cantusdata.models.plugin import Plugin

        families: list[Metric] = []
        with transaction.atomic():
            with connection.cursor() as cursor:
                # SET LOCAL lasts until the end of this transaction only.
                cursor.execute(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")

            manuscripts = GaugeMetricFamily(
                "cantus_manuscripts",
                "Manuscripts by visibility, chant import and folio mapping state.",
                labels=["public", "chants_loaded", "mapping_status"],
            )
            for row in Manuscript.objects.values(
                "public", "chants_loaded", "is_mapped"
            ).annotate(n=Count("pk")):
                manuscripts.add_metric(
                    [
                        _bool_label(row["public"]),
                        _bool_label(row["chants_loaded"]),
                        row["is_mapped"],
                    ],
                    row["n"],
                )
            families.append(manuscripts)

            # Per-manuscript gauges cover the manuscripts anyone works with: the
            # public ones and those with chants imported. The rest are bare
            # CANTUS Database sources, and would only add series.
            tracked = Manuscript.objects.filter(Q(public=True) | Q(chants_loaded=True))
            info = GaugeMetricFamily(
                "cantus_manuscript_info",
                "Always 1; joins manuscript_id to the manuscript's siglum and name.",
                labels=["manuscript_id", "siglum", "name", "public"],
            )
            for pk, siglum, name, public in tracked.values_list(
                "pk", "siglum", "name", "public"
            ):
                info.add_metric(
                    [str(pk), siglum or "", name or "", _bool_label(public)], 1
                )
            families.append(info)

            with_plugin = GaugeMetricFamily(
                "cantus_manuscripts_with_plugin",
                "Manuscripts that have a plugin (e.g. notation search) enabled.",
                labels=["plugin"],
            )
            for plugin in Plugin.objects.annotate(n=Count("plugins")):
                with_plugin.add_metric([plugin.slug], plugin.n)
            families.append(with_plugin)

            folios = GaugeMetricFamily(
                "cantus_folios", "Folios per manuscript.", labels=["manuscript_id"]
            )
            folios_with_image = GaugeMetricFamily(
                "cantus_folios_with_image",
                "Folios mapped to an IIIF image, per manuscript.",
                labels=["manuscript_id"],
            )
            has_image = Q(image_uri__isnull=False) & ~Q(image_uri="")
            for row in (
                Folio.objects.filter(manuscript__in=tracked)
                .values("manuscript_id")
                .annotate(total=Count("pk"), mapped=Count("pk", filter=has_image))
            ):
                folios.add_metric([str(row["manuscript_id"])], row["total"])
                folios_with_image.add_metric([str(row["manuscript_id"])], row["mapped"])
            families.extend([folios, folios_with_image])

            chants = GaugeMetricFamily(
                "cantus_chants", "Chants per manuscript.", labels=["manuscript_id"]
            )
            chants_with_volpiano = GaugeMetricFamily(
                "cantus_chants_with_volpiano",
                "Chants with a melody (volpiano), per manuscript.",
                labels=["manuscript_id"],
            )
            has_volpiano = Q(volpiano__isnull=False) & ~Q(volpiano="")
            for row in (
                Chant.objects.filter(manuscript__in=tracked)
                .values("manuscript_id")
                .annotate(total=Count("pk"), melodic=Count("pk", filter=has_volpiano))
            ):
                chants.add_metric([str(row["manuscript_id"])], row["total"])
                chants_with_volpiano.add_metric(
                    [str(row["manuscript_id"])], row["melodic"]
                )
            families.extend([chants, chants_with_volpiano])

            exemplars = GaugeMetricFamily(
                "cantus_neume_exemplars",
                "Neume exemplars chosen for notation search, per manuscript.",
                labels=["manuscript_id"],
            )
            for row in NeumeExemplar.objects.values("folio__manuscript_id").annotate(
                n=Count("pk")
            ):
                exemplars.add_metric([str(row["folio__manuscript_id"])], row["n"])
            families.append(exemplars)

            families.extend(self._mei_families(MEISubmission, SubmissionStatus))

            records = GaugeMetricFamily(
                "cantus_db_records",
                "Rows of each record type that Solr mirrors (compare cantus_solr_documents).",
                labels=["record_type"],
            )
            for record_type, model in (
                ("manuscript", Manuscript),
                ("folio", Folio),
                ("chant", Chant),
            ):
                records.add_metric([record_type], model.objects.count())
            families.append(records)

            families.extend(self._task_families(TaskResult))

            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            families.append(
                GaugeMetricFamily(
                    "cantus_django_unapplied_migrations",
                    "Migrations the deployed code has that the database has not run.",
                    value=len(plan),
                )
            )
        return families

    def _mei_families(self, MEISubmission: Any, SubmissionStatus: Any) -> list[Metric]:
        by_status = GaugeMetricFamily(
            "cantus_mei_submissions",
            "MEI submissions by review status.",
            labels=["status"],
        )
        counts = dict(
            MEISubmission.objects.values_list("status").annotate(n=Count("pk"))
        )
        for status in SubmissionStatus.values:
            by_status.add_metric([status], counts.get(status, 0))

        now = timezone.now()
        oldest = MEISubmission.objects.aggregate(
            pending=Min("submitted_at", filter=Q(status=SubmissionStatus.PENDING)),
            # A claim sets reviewed_at, so that is when publishing began.
            publishing=Min("reviewed_at", filter=Q(status=SubmissionStatus.PUBLISHING)),
        )
        pending_age = GaugeMetricFamily(
            "cantus_mei_oldest_pending_age_seconds",
            "Age of the oldest submission awaiting review (0 when none).",
            value=(now - oldest["pending"]).total_seconds() if oldest["pending"] else 0,
        )
        publishing_age = GaugeMetricFamily(
            "cantus_mei_oldest_publishing_age_seconds",
            "Time the oldest in-flight publication has been running (0 when none).",
            value=(
                (now - oldest["publishing"]).total_seconds()
                if oldest["publishing"]
                else 0
            ),
        )
        return [by_status, pending_age, publishing_age]

    def _task_families(self, TaskResult: Any) -> list[Metric]:
        results = GaugeMetricFamily(
            "cantus_celery_task_results",
            "Rows in the task results table, by task and state.",
            labels=["task", "status"],
        )
        for row in TaskResult.objects.values("task_name", "status").annotate(
            n=Count("pk")
        ):
            results.add_metric([row["task_name"] or "unknown", row["status"]], row["n"])

        now = timezone.now()
        oldest_unfinished = GaugeMetricFamily(
            "cantus_celery_oldest_unfinished_task_age_seconds",
            "Age of the oldest task that was queued or started and never finished.",
            labels=["task"],
        )
        for row in (
            TaskResult.objects.filter(status__in=UNFINISHED_TASK_STATES)
            .values("task_name")
            .annotate(oldest=Min("date_created"))
        ):
            oldest_unfinished.add_metric(
                [row["task_name"] or "unknown"],
                (now - row["oldest"]).total_seconds(),
            )
        return [results, oldest_unfinished]

    # Solr --------------------------------------------------------------------

    def _solr_families(self) -> list[Metric]:
        from cantusdata.models import Manuscript

        manuscript_ids = list(
            Manuscript.objects.filter(
                Q(public=True) | Q(chants_loaded=True)
            ).values_list("pk", flat=True)
        )
        # manuscript_id is a point field without docValues, which Solr will not
        # facet on, so n-grams are counted with one facet query per manuscript
        # instead -- all in the same request as the document types.
        ngram_queries = {
            f"type:omr_ngram AND manuscript_id:{pk}": str(pk) for pk in manuscript_ids
        }
        response = solr_get(
            "inventory",
            {
                "q": "*:*",
                "rows": 0,
                "facet": "true",
                "facet.field": "type",
                "facet.limit": -1,
                "facet.mincount": 1,
                "facet.query": list(ngram_queries),
            },
            timeout=SOLR_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        facets = response.json()["facet_counts"]

        documents = GaugeMetricFamily(
            "cantus_solr_documents",
            "Documents in the Solr core by type (compare cantus_db_records).",
            labels=["type"],
        )
        for doc_type, count in _facet_pairs(facets["facet_fields"]["type"]):
            documents.add_metric([doc_type], count)

        ngrams = GaugeMetricFamily(
            "cantus_solr_omr_ngrams",
            "Notation-search n-gram documents indexed, per manuscript (0: none).",
            labels=["manuscript_id"],
        )
        for query, count in facets.get("facet_queries", {}).items():
            ngrams.add_metric([ngram_queries[query]], count)
        return [documents, ngrams]
