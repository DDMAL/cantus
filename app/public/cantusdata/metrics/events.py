"""
Recording helpers for business events that need more than a single increment.
"""

import functools
import time
from typing import Any, Callable

from cantusdata.metrics.definitions import (
    ADMIN_LOGINS,
    BACKGROUND_THREAD_FAILURES,
    MEI_REVIEW_LATENCY,
    MEI_REVIEWS,
)


def record_mei_review(submission: Any, action: str, via: str) -> None:
    """A review decision; `submission.reviewed_at` must already be set."""
    MEI_REVIEWS.labels(action, via).inc()
    if submission.reviewed_at and submission.submitted_at:
        MEI_REVIEW_LATENCY.labels(action).observe(
            max(0.0, (submission.reviewed_at - submission.submitted_at).total_seconds())
        )


def counting_failures(thread: str, target: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap a background thread's target so that an exception is counted.

    A thread's exception otherwise only reaches stderr, where nobody looks.
    """

    @functools.wraps(target)
    def run(*args: Any, **kwargs: Any) -> Any:
        try:
            return target(*args, **kwargs)
        except BaseException:
            BACKGROUND_THREAD_FAILURES.labels(thread).inc()
            raise

    return run


def login_succeeded(**kwargs: Any) -> None:
    ADMIN_LOGINS.labels("success").inc()


def login_failed(**kwargs: Any) -> None:
    ADMIN_LOGINS.labels("failure").inc()


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000
