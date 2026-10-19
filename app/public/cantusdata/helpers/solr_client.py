"""
Solr clients with a working timeout, and with every request measured.

solrpy accepts a `timeout` argument but only hands it to http.client on Python 2
(solr/core.py compares the interpreter version), so on Python 3 a hung Solr
blocks the caller indefinitely -- and solrpy then retries the socket error up to
`max_retries` times. `make_solr` sets the timeout on the underlying connection
instead, which http.client applies on every (re)connect.
"""

from typing import Any, Optional, Type, TypeVar

import requests
import solr
from django.conf import settings

from cantusdata.metrics.tracking import track_solr


class _InstrumentedMixin:
    metrics_operation = "unknown"

    def _post(self, url: str, body: str, headers: dict[str, str]) -> Any:
        # Every solrpy request -- select, update, delete, commit -- goes through
        # _post, so this is the one place to measure them.
        with track_solr(self.metrics_operation):
            return super()._post(url, body, headers)  # type: ignore[misc]


class InstrumentedSolr(_InstrumentedMixin, solr.Solr):
    pass


class InstrumentedSolrConnection(_InstrumentedMixin, solr.SolrConnection):
    pass


SolrClient = TypeVar("SolrClient", InstrumentedSolr, InstrumentedSolrConnection)


def make_solr(
    operation: str,
    *,
    cls: Type[SolrClient] = InstrumentedSolrConnection,  # type: ignore[assignment]
    url: Optional[str] = None,
    timeout: Optional[float] = None,
    max_retries: int = 1,
) -> SolrClient:
    """
    A solrpy client labelled `operation` in the Solr request metrics.

    timeout defaults to SOLR_TIMEOUT; indexing and maintenance commands that
    send large batches should pass SOLR_INDEX_TIMEOUT.
    """
    client = cls(url or settings.SOLR_SERVER, max_retries=max_retries)
    client.metrics_operation = operation
    client.conn.timeout = settings.SOLR_TIMEOUT if timeout is None else timeout
    return client


def solr_get(
    operation: str,
    params: dict[str, Any],
    *,
    timeout: Optional[float] = None,
) -> requests.Response:
    """
    GET {SOLR_SERVER}/select with `params`, measured as `operation`.

    The response is returned whatever its status, as requests does; an error
    status is still recorded as a failed request.
    """
    with track_solr(operation) as tracked:
        response = requests.get(
            f"{settings.SOLR_SERVER}/select",
            params=params,
            timeout=settings.SOLR_TIMEOUT if timeout is None else timeout,
        )
        if response.status_code >= 400:
            tracked.outcome = "error"
    return response
