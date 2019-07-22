#!/bin/bash

echo "===== Setting up django ====="
cd public
virtualenv app_env
source app_env/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

python manage.py makemigrations
python manage.py migrate

