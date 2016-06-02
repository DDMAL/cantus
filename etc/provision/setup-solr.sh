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

# Solr support
java_version=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')

if [[ "$java_version" != "1.8"* ]]; then
    echo "Adding Java 8 PPA and updating package lists..."
    sudo add-apt-repository -y ppa:openjdk-r/ppa
    sudo apt-get -qq update

    sudo apt-get install -y --no-install-recommends openjdk-8-jdk

    # FIXME: I don't really know if this is the right thing to do
    sudo update-alternatives --install /usr/bin/java  java  /usr/lib/jvm/java-8-openjdk-i386/jre/bin/java 2000
    sudo update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-8-openjdk-i386/bin/javac    2000
fi

solr_version=6.0.1

# FIXME: Get a better way of checking the current Solr version
if [ ! `which solr` ] || [[  `readlink -f $( which solr )` != *"solr-$solr_version"* ]]; then
    (
        echo "Installing Solr $solr_version..."

        mkdir -p ~/solr
        cd ~/solr

        url="https://www.apache.org/dist/lucene/solr/$solr_version/solr-$solr_version.tgz"

        echo "Downloading Solr from $url..."
        curl -sS -L "$url" -o "solr-$solr_version.tgz"
        tar xzf "solr-$solr_version.tgz"

        # FIXME: there should really be a nicer way of doing installation
        sudo ln -fs "`pwd`/solr-$solr_version/bin/solr" /usr/local/bin/solr

        # Symlink the Solr config directory from Cantus into the server directory
        mkdir -p                        "./solr-$solr_version/server"
        rm -r                           "./solr-$solr_version/server/solr"
        ln -s /vagrant/public/solr/solr "./solr-$solr_version/server/solr"

        echo "Solr installed!"
    )
fi

echo "===================== INSTALLING SOLR ====================="

# Set up relevant runtime paths
if [ ! -d /var/db/solr ]; then
    sudo mkdir -p /var/db/solr
    sudo chgrp www-data /var/db/solr
fi
