#!/bin/bash

# Exit whenever a command throws a return value != 0
set -e

# None or one arguments allowed. If one, the argument is the root directory. If none, this is the root directory
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

