#!/bin/bash

echo "===== Setting up django ====="
cd public
virtualenv app_env
source app_env/bin/activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

echo "===== Build the static files ====="
cd cantusdata/frontend
npm install
gulp build --release