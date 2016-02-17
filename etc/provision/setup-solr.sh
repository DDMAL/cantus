#!/bin/bash

set -e

if [ "$#" -eq 1 ]; then
    ROOT=$1
elif [ "$#" -eq 0 ]; then
    ROOT=.
else
    echo "Usage: $0 [root_path]"
    exit 1
fi


echo "=========== INSTALLING JAVA SYSTEM DEPENDENCIES ==========="

sudo apt-get install -y --no-install-recommends openjdk-7-jdk
javac -version

sudo apt-get install -y maven


echo "===================== INSTALLING SOLR ====================="

# Set up relevant runtime paths
if [ ! -d /var/db/solr ]; then
    sudo mkdir -p /var/db/solr
    sudo chgrp www-data /var/db/solr
fi
