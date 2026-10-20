#!/bin/bash

python manage.py clear_session_data
python manage.py collectstatic --noinput

if [[ $DEVELOPMENT == "True" ]]; then
    python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:3000 manage.py runserver_plus 0:8001 --nopin
else
    # Workers write their metrics here and the master serves the merged values
    # (gunicorn.conf.py). Exported here, not in the pod spec, so that manage.py
    # run through `kubectl exec` keeps to its own in-process registry.
    export PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus-multiproc}"
    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
    find "$PROMETHEUS_MULTIPROC_DIR" -mindepth 1 -delete
    exec gunicorn -c /code/gunicorn.conf.py cantusdata.wsgi
fi
