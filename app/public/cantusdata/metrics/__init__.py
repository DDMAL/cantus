"""
Prometheus instrumentation for Cantus Ultimus.

Every metric is defined in `definitions`, so names and labels stay consistent
across the web workers, the Celery worker and the metrics exporter. Label values
are produced by `labels`, which keeps them bounded: nothing a request controls
(query text, arbitrary ids, URLs, user agents) ever becomes a label value as-is.

Web and worker processes run in prometheus_client's multiprocess mode. Their
launcher scripts export PROMETHEUS_MULTIPROC_DIR, and gunicorn's master and the
Celery main process serve the merged values (see `multiprocess`). Anything
started any other way -- tests, `manage.py` run through `kubectl exec`, the
Celery liveness probe -- uses the ordinary in-process registry instead.
"""
