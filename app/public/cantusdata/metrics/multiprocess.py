"""
Serving metrics from processes that fork workers (gunicorn, Celery prefork).

Each worker process writes its values to files under PROMETHEUS_MULTIPROC_DIR;
the parent process merges them on every scrape. The parent never handles
requests or tasks, so serving from it keeps scrapes working while every worker
is busy.
"""

import os
from typing import Optional

from prometheus_client import CollectorRegistry, multiprocess, start_http_server


def enabled() -> bool:
    return bool(os.environ.get("PROMETHEUS_MULTIPROC_DIR"))


def serve(port: int) -> None:
    """Serve the merged values of every process sharing the directory on `port`."""
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    start_http_server(port, registry=registry)


def mark_dead(pid: Optional[int] = None) -> None:
    """Drop a finished process's live gauges (its counters are kept, as they should be)."""
    if enabled():
        multiprocess.mark_process_dead(pid if pid is not None else os.getpid())
