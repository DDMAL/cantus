"""
gunicorn settings for deployed environments (see django-config.sh).

The workers write their Prometheus metrics to PROMETHEUS_MULTIPROC_DIR, and the
master serves the merged values on METRICS_PORT -- the master never handles a
request itself, so scrapes still answer when every worker is busy. Port 8001 is
proxied publicly by nginx, which is why metrics are not served there.
"""

import os

bind = "0.0.0.0:8001"
workers = int(os.environ.get("GUNICORN_WORKERS", "4"))
timeout = 600

METRICS_PORT = int(os.environ.get("GUNICORN_METRICS_PORT", "9100"))


def when_ready(server):
    from cantusdata.metrics import multiprocess
    from cantusdata.metrics.definitions import GUNICORN_WORKERS

    GUNICORN_WORKERS.set(workers)
    multiprocess.serve(METRICS_PORT)


def child_exit(server, worker):
    from cantusdata.metrics import multiprocess
    from cantusdata.metrics.definitions import GUNICORN_WORKER_EXITS

    GUNICORN_WORKER_EXITS.inc()
    multiprocess.mark_dead(worker.pid)


def worker_abort(worker):
    # Called in a worker the master is killing for exceeding `timeout`.
    from cantusdata.metrics.definitions import GUNICORN_WORKER_TIMEOUTS

    GUNICORN_WORKER_TIMEOUTS.inc()
