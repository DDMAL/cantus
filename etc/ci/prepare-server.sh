#!/bin/bash

set -e

# Run Solr and poll until it's ready

cd ./public

solr start -p 8080

solr status

source app_env/bin/activate

cp ./cantusdata/settings-example.py ./cantusdata/settings.py

# ./manage.py wait_until_solr_ready --timeout=90

./manage.py makemigrations
./manage.py migrate
