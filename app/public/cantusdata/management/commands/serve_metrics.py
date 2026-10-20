import threading
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from prometheus_client import CollectorRegistry, start_http_server

from cantusdata.metrics.build import build_labels
from cantusdata.metrics.inventory import InventoryCollector


class Command(BaseCommand):
    help = (
        "Serve the collection's inventory gauges (manuscripts, data coverage, "
        "MEI review queue, Solr drift, stuck tasks) for Prometheus. Runs as the "
        "metrics-exporter Deployment; see cantusdata/metrics/inventory.py."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--port", type=int, default=9102)

    def handle(self, *args: Any, **options: Any) -> None:
        # A registry of its own: the default one holds this process's request
        # and query metrics, which mean nothing for an exporter.
        registry = CollectorRegistry()
        registry.register(InventoryCollector(build_labels=build_labels()))
        start_http_server(options["port"], registry=registry)
        self.stdout.write(f"Serving inventory metrics on port {options['port']}")
        threading.Event().wait()
