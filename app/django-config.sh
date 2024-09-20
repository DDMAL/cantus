#!/bin/bash

python manage.py clear_session_data
python manage.py collectstatic --noinput

if [[ $DEVELOPMENT == "True" ]]; then
    python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:3000 manage.py runserver_plus 0:8001
else
    gunicorn -b 0:8001 cantusdata.wsgi --timeout 600 --workers 4
fi