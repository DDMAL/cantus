#!/bin/bash

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python /code/public/manage.py runserver 0:8000