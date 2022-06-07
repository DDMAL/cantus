#!/bin/bash

python manage.py makemigrations
python manage.py migrate &
python manage.py clear_session_data

if [[ $APP_PORT = 80 ]]; then
    gunicorn -b 0:8001 cantusdata.wsgi --timeout 600 --workers 4
else
    python manage.py runserver 0:8001
fi