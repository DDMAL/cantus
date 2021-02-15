#!/bin/bash

echo "==== Enable python dev, venv, and pip ===="
apt-get update
apt-get install -y python3-dev python3-venv python3-pip

echo "===== Initial dependencies ====="
apt-get install -y build-essential libxml2-dev libxslt-dev libxslt1-dev zlib1g-dev libjpeg8-dev libpq-dev
ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib

echo "===== Setup postgres ====="
apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "create user cantus_admin with encrypted password 'Pl4c3H0ld3r';"
sudo -u postgres psql -c "alter user cantus_admin with SUPERUSER;"
sudo -u postgres psql -c "create database cantus_db with owner cantus_admin;"

echo "===== Copy the repository ====="
cp -R /vagrant/* /home/$HOMEUSER/
sudo chown -R $HOMEUSER /home/$HOMEUSER/

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
ln -s /home/$HOMEUSER/solr/solr/collection1 /var/solr/data/collection1
ln -s /home/$HOMEUSER/solr/solr/cantus-test /var/solr/data/cantus-test
rm /var/solr/data/solr.xml
ln -s /home/$HOMEUSER/solr/solr/solr.xml /var/solr/data/solr.xml

# Create the folders where the solr data is going to be written
mkdir -p /var/db/solr/
mkdir -p /var/db/solr/cantusdata-solr
chown solr:solr /var/db/solr -R

# Restart solr
service solr restart

echo "===== Installing nodejs/npm ====="
# Cannot use the default node package from apt because it is obsolete
# The last version of node compatible with Ubuntu 14.04 is 8.x, using that
curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
apt-get install -y nodejs
npm install -g gulp
