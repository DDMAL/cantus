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
sudo apt-get update

# "$ROOT/etc/provision/setup-django.sh" "$ROOT"
# "$ROOT/etc/provision/setup-solr.sh" "$ROOT"
# "$ROOT/etc/provision/setup-pymei.sh" "$ROOT"

# Additional packages

sudo apt install -y build-essential libxml2-dev libxslt-dev libxslt1-dev zlib1g-dev libjpeg8-dev libpq-dev python-dev

sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib

# Create the cantus user 
sudo groupadd --system webapps
sudo useradd --system --gid webapps --shell /bin/bash --home /srv/webapps/cantus cantus
sudo echo "cantus ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Setup postgres
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "create user cantus_admin with encrypted password '${CANTUS_ADMIN_PASSWORD}';"
sudo -u postgres psql -c "alter user cantus_admin with SUPERUSER;"
sudo -u postgres psql -c "create database cantus_db with owner cantus_admin;"

# Copy the repository
sudo mkdir -p /srv/webapps/cantus/
sudo cp -R /vagrant/* /srv/webapps/cantus/
sudo chown -R cantus /srv/webapps/cantus/
