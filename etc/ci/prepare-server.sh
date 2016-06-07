#!/bin/bash

set -e

# Run Solr and poll until it's ready

cd ./public

cd ./public

(
    cd solr

    # The `which mvn` seems to be a necessary workaround for some kind of path reset problem
    # FIXME: The output here probably shouldn't be swallowed
    sudo `which mvn` jetty:run-war > /dev/null 2>&1 &
)

solr status

source app_env/bin/activate

cp ./cantusdata/settings-example.py ./cantusdata/settings.py

./manage.py wait_until_solr_ready --timeout=90

./manage.py makemigrations
./manage.py migrate
