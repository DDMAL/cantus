#!/bin/bash

# # Exit whenever a command throws a return value != 0
# set -e

# # None or one arguments allowed. If one, the argument is the root directory. If none, this is the root directory
# if [ "$#" -eq 1 ]; then
#     ROOT=$1
# elif [ "$#" -eq 0 ]; then
#     ROOT=`pwd`
# else
#     echo "Usage: $0 [root_path]"
#     exit 1
# fi

echo "===== Updating package listings ====="
sudo apt-get update

# "$ROOT/etc/provision/setup-django.sh" "$ROOT"
# "$ROOT/etc/provision/setup-solr.sh" "$ROOT"
# "$ROOT/etc/provision/setup-pymei.sh" "$ROOT"

echo "===== Initial dependencies ====="
sudo apt install -y build-essential libxml2-dev libxslt-dev libxslt1-dev zlib1g-dev libjpeg8-dev libpq-dev python-dev
sudo ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib
 
echo "===== Create the cantus user ====="
sudo groupadd --system webapps
sudo useradd --system --gid webapps --shell /bin/bash --home /srv/webapps/cantus cantus
sudo echo "cantus ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

echo "===== Setup postgres ====="
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "create user cantus_admin with encrypted password '${CANTUS_ADMIN_PASSWORD}';"
sudo -u postgres psql -c "alter user cantus_admin with SUPERUSER;"
sudo -u postgres psql -c "create database cantus_db with owner cantus_admin;"

echo "===== Copy the repository ====="
sudo mkdir -p /srv/webapps/cantus/
sudo cp -R /vagrant/* /srv/webapps/cantus/
sudo chown -R cantus:webapps /srv/webapps/cantus/

echo "===== Installing Java 8 ====="
sudo add-apt-repository ppa:openjdk-r/ppa
sudo apt-get update
sudo apt-get install -y openjdk-8-jdk

echo "===== Installing solr ====="
curl -sS -L "http://archive.apache.org/dist/lucene/solr/6.1.0/solr-6.1.0.tgz" -o "solr-6.1.0.tgz"
tar xzf solr-6.1.0.tgz solr-6.1.0/bin/install_solr_service.sh --strip-components=2
sudo bash ./install_solr_service.sh solr-6.1.0.tgz

# Make a symbolic link to the cantus core and solr.xml in the home folder of solr
sudo ln -s /srv/webapps/cantus/public/solr/solr/collection1 /var/solr/data/collection1
sudo ln -s /srv/webapps/cantus/public/solr/solr/cantus-test /var/solr/data/cantus-test
sudo rm /var/solr/data/solr.xml
sudo ln -s /srv/webapps/cantus/public/solr/solr/solr.xml /var/solr/data/solr.xml

# Create the folders where the solr data is going to be written
sudo mkdir -p /var/db/solr/
sudo mkdir -p /var/db/solr/cantusdata-solr
sudo chown solr:solr /var/db/solr -R

echo "===== Setting up django ====="
sudo apt install -y python-virtualenv
sudo su - cantus
cd public
virtualenv app_env
source app_env/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp cantusdata/settings-example.py cantusdata/settings.py
