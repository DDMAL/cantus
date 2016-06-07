#!/bin/bash

set -e

# Run Solr and poll until it's ready

cd ./public

solr start -p 8080

source app_env/bin/activate

cp ./cantusdata/settings-example.py ./cantusdata/settings.py

solr status

./manage.py wait_until_solr_ready --timeout=20000

./manage.py makemigrations
./manage.py migrate
