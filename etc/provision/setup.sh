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
apt-get update

# "$ROOT/etc/provision/setup-django.sh" "$ROOT"
# "$ROOT/etc/provision/setup-solr.sh" "$ROOT"
# "$ROOT/etc/provision/setup-pymei.sh" "$ROOT"

echo "===== Initial dependencies ====="
apt-get install -y build-essential libxml2-dev libxslt-dev libxslt1-dev zlib1g-dev libjpeg8-dev libpq-dev python-dev python-virtualenv
ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib
 
# echo "===== Create the cantus user ====="
# groupadd --system webapps
# useradd --system --gid webapps --shell /bin/bash --home /srv/webapps/cantus cantus
# echo "cantus ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

echo "===== Setup postgres ====="
apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "create user cantus_admin with encrypted password 'Pl4c3H0ld3r';"
sudo -u postgres psql -c "alter user cantus_admin with SUPERUSER;"
sudo -u postgres psql -c "create database cantus_db with owner cantus_admin;"

echo "===== Copy the repository ====="
# sudo mkdir -p /srv/webapps/cantus/
cp -R /vagrant/* .
sudo chown -R vagrant .

echo "===== Installing Java 8 ====="
add-apt-repository ppa:openjdk-r/ppa
apt-get update
apt-get install -y openjdk-8-jdk

echo "===== Installing solr ====="
curl -sS -L "http://archive.apache.org/dist/lucene/solr/6.1.0/solr-6.1.0.tgz" -o "solr-6.1.0.tgz"
tar xzf solr-6.1.0.tgz solr-6.1.0/bin/install_solr_service.sh --strip-components=2
sudo bash ./install_solr_service.sh solr-6.1.0.tgz
# Remove the solr installer
rm solr-6.1.0.tgz
rm install_solr_service.sh

# Make a symbolic link to the cantus core and solr.xml in the home folder of solr
ln -s /home/vagrant/public/solr/solr/collection1 /var/solr/data/collection1
ln -s /home/vagrant/public/solr/solr/cantus-test /var/solr/data/cantus-test
rm /var/solr/data/solr.xml
ln -s /home/vagrant/public/solr/solr/solr.xml /var/solr/data/solr.xml

# Create the folders where the solr data is going to be written
mkdir -p /var/db/solr/
mkdir -p /var/db/solr/cantusdata-solr
chown solr:solr /var/db/solr -R

# Restart solr
service solr restart