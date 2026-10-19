#!/bin/bash

# The pool's child processes write task metrics here and the worker's main
# process serves the merged values (cantusdata/metrics/celery_signals.py).
# Exported here, not in the pod spec, so that the liveness probe's
# `celery inspect ping` and `kubectl exec` keep to their own in-process registry.
export PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus-multiproc}"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
find "$PROMETHEUS_MULTIPROC_DIR" -mindepth 1 -delete
exec /code/.venv/bin/celery -A cantusdata worker -l INFO -c 1
