#!/bin/bash

python manage.py makemigrations
python manage.py migrate &
python manage.py clear_session_data
python manage.py collectstatic --noinput

if [[ $APP_PORT = 80 ]]; then
    gunicorn -b 0:8001 cantusdata.wsgi --timeout 600 --workers 4
else
    python manage.py runserver_plus 0:8001
fi