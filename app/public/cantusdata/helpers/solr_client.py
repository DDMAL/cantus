"""
Solr clients with a working timeout, and with every request measured.

solrpy accepts a `timeout` argument but only hands it to http.client on Python 2
(solr/core.py compares the interpreter version), so on Python 3 a hung Solr
blocks the caller indefinitely -- and solrpy then retries the socket error up to
`max_retries` times. `make_solr` sets the timeout on the underlying connection
instead, which http.client applies on every (re)connect.
"""

import http.client
from typing import Any, Optional, Type, TypeVar

import requests
import solr
from django.conf import settings
from rest_framework.exceptions import APIException

from cantusdata.metrics.tracking import track_solr


class SolrUnavailable(APIException):
    """
    Solr could not be reached, timed out, or answered with a server error.

    An API view that lets it propagate answers 502; elsewhere it is an ordinary
    exception, with the original error as its __cause__.
    """

    status_code = 502
    default_detail = "Search is unavailable right now."
    default_code = "solr_unavailable"


class _InstrumentedMixin:
    metrics_operation = "unknown"

    def _post(self, url: str, body: str, headers: dict[str, str]) -> Any:
        # Every solrpy request -- select, update, delete, commit -- goes through
        # _post, so this is the one place to measure them, and to turn Solr
        # being down into SolrUnavailable. A 4xx SolrException is Solr refusing
        # the request itself, and is left for the caller.
        try:
            with track_solr(self.metrics_operation):
                return super()._post(url, body, headers)  # type: ignore[misc]
        except (OSError, http.client.HTTPException) as exc:
            raise SolrUnavailable() from exc
        except solr.SolrException as exc:
            if exc.httpcode is None or exc.httpcode >= 500:
                raise SolrUnavailable() from exc
            raise


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

    Raises SolrUnavailable when Solr cannot be reached, times out or answers
    5xx. Any other response is returned whatever its status, as requests does;
    a 4xx is still recorded as a failed request.
    """
    try:
        with track_solr(operation) as tracked:
            response = requests.get(
                f"{settings.SOLR_SERVER}/select",
                params=params,
                timeout=settings.SOLR_TIMEOUT if timeout is None else timeout,
            )
            if response.status_code >= 400:
                tracked.outcome = "error"
    except requests.RequestException as exc:
        raise SolrUnavailable() from exc
    if response.status_code >= 500:
        raise SolrUnavailable()
    return response
