#!/bin/bash

set -e

# Run Solr and poll until it's ready

cd ./public

(
    cd solr

    # The `which mvn` seems to be a necessary workaround for some kind of path reset problem
    # FIXME: The output here probably shouldn't be swallowed
    sudo `which mvn` jetty:run-war > /dev/null 2>&1 &
)

source app_env/bin/activate

./manage.py wait_until_solr_ready
