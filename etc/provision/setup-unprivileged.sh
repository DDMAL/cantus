#!/bin/bash

echo "===== Setting up django ====="
cd public
virtualenv app_env
python3.5 -m venv app_env3
source app_env3/bin/activate
pip install -r requirements3.txt

python manage.py makemigrations
python manage.py migrate

echo "===== Build the static files ====="
cd cantusdata/frontend
npm install
gulp build --release