#!/bin/bash

set -e

# Run Solr and poll until it's ready

cd ./public

# Print the current working directory
pwd

solr -h
echo "Starting Solr"
#solr start -p 8080
#echo "Getting Solr Status"
#solr status

(
    cd /home/travis
    ls
    cd solr
    ls
    cd solr-6.0.1
    ls
    cd server
    ls -l
    cd solr
    echo "In Solr"
    ls
)

solr start -p 8080

solr status

source app_env/bin/activate

cp ./cantusdata/settings-example.py ./cantusdata/settings.py

./manage.py wait_until_solr_ready --timeout=90

./manage.py makemigrations
./manage.py migrate
