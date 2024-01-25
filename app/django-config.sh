#!/bin/bash

python manage.py clear_session_data

if [[ $DEVELOPMENT == "True" ]]; then
    python manage.py runserver_plus 0:8001
else
    gunicorn -b 0:8001 cantusdata.wsgi --timeout 600 --workers 4
fi