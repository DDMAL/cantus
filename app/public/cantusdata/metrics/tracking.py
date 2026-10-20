"""
Timing and outcome tracking for calls to Solr and to services outside the cluster.

Both context managers yield a `Tracked` whose `outcome` the caller may set, for
calls that report failure through a status code rather than an exception.
"""

import time
from contextlib import contextmanager
from typing import Iterator

import requests

from cantusdata.metrics.definitions import (
    EXTERNAL_REQUEST_DURATION,
    EXTERNAL_REQUESTS,
    SOLR_REQUEST_DURATION,
    SOLR_REQUESTS,
)
from cantusdata.metrics.labels import upstream_host_label


class Tracked:
    def __init__(self) -> None:
        self.outcome = "success"


def outcome_of(exc: BaseException) -> str:
    # socket.timeout is TimeoutError; urllib wraps it in URLError.reason;
    # requests' timeouts are their own hierarchy.
    if isinstance(exc, (TimeoutError, requests.Timeout)):
        return "timeout"
    if isinstance(getattr(exc, "reason", None), TimeoutError):
        return "timeout"
    return "error"


@contextmanager
def track_solr(operation: str) -> Iterator[Tracked]:
    tracked = Tracked()
    start = time.perf_counter()
    try:
        yield tracked
    except BaseException as exc:
        tracked.outcome = outcome_of(exc)
        raise
    finally:
        SOLR_REQUEST_DURATION.labels(operation).observe(time.perf_counter() - start)
        SOLR_REQUESTS.labels(operation, tracked.outcome).inc()


@contextmanager
def track_external(target: str, url: str) -> Iterator[Tracked]:
    tracked = Tracked()
    start = time.perf_counter()
    try:
        yield tracked
    except BaseException as exc:
        tracked.outcome = outcome_of(exc)
        raise
    finally:
        EXTERNAL_REQUEST_DURATION.labels(target).observe(time.perf_counter() - start)
        EXTERNAL_REQUESTS.labels(
            target, upstream_host_label(url), tracked.outcome
        ).inc()
