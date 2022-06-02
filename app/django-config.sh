#!/bin/bash

python manage.py makemigrations
python manage.py migrate &

gunicorn -b 0:8001 cantusdata.wsgi --timeout 600 --workers 4