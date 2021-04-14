#!/bin/bash

echo "===== Setting the home user ====="
echo "export HOMEUSER=${HOMEUSER}" >> /etc/profile.d/cantus.sh

echo "===== Setting the django secret key ====="
if [ -z $SECRET_KEY ]
then
    echo "===== No django secret key provided, generate one ====="
    export SECRET_KEY=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 64)
    echo "SECRET_KEY is $SECRET_KEY"
fi
echo "export SECRET_KEY=${SECRET_KEY}" >> /etc/profile.d/cantus.sh


echo "===== Setting the environment as either staging or production ====="
if [ -z ${IS_PRODUCTION+x} ]
then
    echo "===== This is a STAGING environment ====="
else
    echo "===== This is a PRODUCTION environment ====="
    echo "export IS_PRODUCTION=${IS_PRODUCTION}" >> /etc/profile.d/cantus.sh
fi

# TODO: Any other environment variables