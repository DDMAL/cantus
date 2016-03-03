#!/bin/bash

set -e

if [ "$#" -eq 1 ]; then
    ROOT=$1
elif [ "$#" -eq 0 ]; then
    ROOT=`pwd`
else
    echo "Usage: $0 [root_path]"
    exit 1
fi


echo "=========== INSTALLING JAVA SYSTEM DEPENDENCIES ==========="

# FIXME: For now, we're just assuming that if some version of Java
# and Maven are installed, we can use them

if [ ! `which java` ]; then
    sudo apt-get install -y --no-install-recommends openjdk-7-jdk
    javac -version
fi

if [ ! `which mvn` ]; then
    sudo apt-get install -y maven
fi


echo "===================== INSTALLING SOLR ====================="

# Set up relevant runtime paths
if [ ! -d /var/db/solr ]; then
    sudo mkdir -p /var/db/solr
    sudo chgrp www-data /var/db/solr
fi
