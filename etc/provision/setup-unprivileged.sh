#!/bin/bash

echo "===== Setting up django ====="
cd public
python3 -m venv app_env
source app_env/bin/activate
pip install -r requirements.txt


echo "===== Initializing django ====="
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput


echo "===== Build the static files ====="
cd cantusdata/frontend
npm install
gulp build --release