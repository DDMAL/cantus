"""
Celery task metrics, from Celery's own signals.

Publishing is counted wherever a task is sent (web workers, admin threads).
Everything else is counted in the worker: `task_received` in the main process,
the execution signals in the prefork child that runs the task. The main process
serves both on CELERY_METRICS_PORT.
"""

import os
import time
from typing import Any

from celery import signals

from cantusdata.metrics import multiprocess
from cantusdata.metrics.definitions import (
    CELERY_TASK_DURATION,
    CELERY_TASK_QUEUE_WAIT,
    CELERY_TASK_RUNS,
    CELERY_TASKS_IN_PROGRESS,
    CELERY_TASKS_PUBLISHED,
    CELERY_TASKS_RECEIVED,
)

PUBLISHED_AT_HEADER = "cantus_published_at"
CELERY_METRICS_PORT = int(os.environ.get("CELERY_METRICS_PORT", "9101"))

# task id -> perf_counter at prerun, in the process running the task.
_started: dict[str, float] = {}


@signals.before_task_publish.connect
def stamp_publish_time(headers: Any = None, **kwargs: Any) -> None:
    # A custom message header reaches the worker as an attribute of task.request.
    if headers is not None:
        headers[PUBLISHED_AT_HEADER] = time.time()


@signals.after_task_publish.connect
def count_published(sender: Any = None, **kwargs: Any) -> None:
    CELERY_TASKS_PUBLISHED.labels(str(sender)).inc()


@signals.worker_init.connect
def serve_worker_metrics(**kwargs: Any) -> None:
    # Only the worker's main process: it outlives the pool's children, and is
    # free to answer scrapes while a child is busy with a long import.
    if multiprocess.enabled():
        multiprocess.serve(CELERY_METRICS_PORT)


@signals.worker_process_shutdown.connect
def drop_child_gauges(**kwargs: Any) -> None:
    multiprocess.mark_dead()


@signals.task_received.connect
def count_received(request: Any = None, **kwargs: Any) -> None:
    CELERY_TASKS_RECEIVED.labels(request.task_name).inc()


@signals.task_prerun.connect
def task_started(task_id: str = "", task: Any = None, **kwargs: Any) -> None:
    _started[task_id] = time.perf_counter()
    CELERY_TASKS_IN_PROGRESS.labels(task.name).inc()
    published_at = getattr(task.request, PUBLISHED_AT_HEADER, None)
    if published_at is not None:
        CELERY_TASK_QUEUE_WAIT.labels(task.name).observe(
            max(0.0, time.time() - float(published_at))
        )


@signals.task_postrun.connect
def task_finished(
    task_id: str = "", task: Any = None, state: Any = None, **kwargs: Any
) -> None:
    CELERY_TASKS_IN_PROGRESS.labels(task.name).dec()
    started = _started.pop(task_id, None)
    if started is not None:
        CELERY_TASK_DURATION.labels(task.name).observe(time.perf_counter() - started)
    # Failures and retries are counted by their own signals, which carry the
    # detail; postrun only settles successes.
    if state == "SUCCESS":
        CELERY_TASK_RUNS.labels(task.name, "success").inc()


@signals.task_failure.connect
def task_failed(sender: Any = None, **kwargs: Any) -> None:
    CELERY_TASK_RUNS.labels(sender.name, "failure").inc()


@signals.task_retry.connect
def task_retried(sender: Any = None, **kwargs: Any) -> None:
    CELERY_TASK_RUNS.labels(sender.name, "retry").inc()


@signals.task_revoked.connect
def task_revoked(request: Any = None, **kwargs: Any) -> None:
    CELERY_TASK_RUNS.labels(request.task_name, "revoked").inc()
