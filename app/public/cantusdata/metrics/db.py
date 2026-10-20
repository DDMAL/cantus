"""
Database query metrics, via Django's execute_wrapper hook.

The wrapper is attached to every connection as it is opened, so it sees ORM and
raw queries alike in every process. A request counts its own queries through a
context variable that MetricsMiddleware sets.
"""

import time
from contextvars import ContextVar, Token
from typing import Any, Callable, Optional

from cantusdata.metrics.definitions import DB_ERRORS, DB_QUERIES, DB_QUERY_DURATION

_request_query_count: ContextVar[Optional[list[int]]] = ContextVar(
    "cantus_request_query_count", default=None
)

_OPERATIONS = ("select", "insert", "update", "delete")


def _operation(sql: str) -> str:
    head = sql.lstrip()[:6].lower()
    return head if head in _OPERATIONS else "other"


def _record_query(
    execute: Callable[..., Any], sql: str, params: Any, many: bool, context: Any
) -> Any:
    operation = _operation(sql)
    count = _request_query_count.get()
    if count is not None:
        count[0] += 1
    start = time.perf_counter()
    try:
        result = execute(sql, params, many, context)
    except Exception as exc:
        DB_QUERIES.labels(operation, "error").inc()
        DB_ERRORS.labels(type(exc).__name__).inc()
        raise
    finally:
        DB_QUERY_DURATION.labels(operation).observe(time.perf_counter() - start)
    DB_QUERIES.labels(operation, "ok").inc()
    return result


def install_query_wrapper(sender: Any, connection: Any, **kwargs: Any) -> None:
    """connection_created receiver."""
    if _record_query not in connection.execute_wrappers:
        connection.execute_wrappers.append(_record_query)


def start_request_count() -> Token[Optional[list[int]]]:
    return _request_query_count.set([0])


def finish_request_count(token: Token[Optional[list[int]]]) -> int:
    count = _request_query_count.get()
    _request_query_count.reset(token)
    return count[0] if count is not None else 0
