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

echo "Updating package listings"
sudo apt-get -qq update

"$ROOT/etc/provision/setup-django.sh" "$ROOT"
"$ROOT/etc/provision/setup-solr.sh" "$ROOT"
"$ROOT/etc/provision/setup-pymei.sh" "$ROOT"

