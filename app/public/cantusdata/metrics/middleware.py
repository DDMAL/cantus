import time
from typing import Any, Callable

from django.http import HttpRequest, HttpResponse

from cantusdata.metrics.db import finish_request_count, start_request_count
from cantusdata.metrics.definitions import (
    HTTP_EXCEPTIONS,
    HTTP_REQUEST_DB_QUERIES,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_RESPONSE_SIZE,
    PAGE_LOADS,
)
from cantusdata.metrics.labels import classify_client, method_label, route_label

# Routes that render a full page when asked for HTML: the single-page app's
# shell (the client then fetches the same routes as JSON) and the static pages.
PAGE_ROUTES = frozenset(
    {
        "homepage",
        "about",
        "team",
        "activities",
        "manifests",
        "manuscript-list",
        "manuscript-detail",
        "search-view",
    }
)


class MetricsMiddleware:
    """
    Request rate, errors, latency and saturation for every request Django serves.

    Listed first in MIDDLEWARE so that it times the whole stack, and sees the
    response every other middleware has finished with.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        token = start_request_count()
        HTTP_REQUESTS_IN_PROGRESS.inc()
        try:
            response = self.get_response(request)
        finally:
            HTTP_REQUESTS_IN_PROGRESS.dec()
            query_count = finish_request_count(token)
        elapsed = time.perf_counter() - start

        route = route_label(request)
        method = method_label(request)
        client = classify_client(request)
        HTTP_REQUEST_DURATION.labels(method, route).observe(elapsed)
        HTTP_REQUESTS.labels(method, route, str(response.status_code), client).inc()
        HTTP_REQUEST_DB_QUERIES.labels(route).observe(query_count)
        if not response.streaming:
            HTTP_RESPONSE_SIZE.labels(route).observe(len(response.content))
        if (
            route in PAGE_ROUTES
            and response.status_code == 200
            and response.get("Content-Type", "").startswith("text/html")
        ):
            PAGE_LOADS.labels(route, client).inc()
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> Any:
        HTTP_EXCEPTIONS.labels(route_label(request), type(exception).__name__).inc()
        return None
