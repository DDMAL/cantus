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


echo "========== INSTALLING PYTHON SYSTEM DEPENDENCIES =========="

django_system_dependencies=(
    python2.7-dev python-openssl python-pip

    # Postgres support
    libpq-dev postgresql-server-dev-9.3

    # Needed for lxml
    libxml2-dev libxslt1-dev
    )

sudo apt-get install -y ${django_system_dependencies[@]}
sudo pip install virtualenv


echo "==================== INSTALLING DJANGO ===================="

(
    cd "$ROOT/public"

    if [ ! -d app_env ]; then
         virtualenv app_env
    fi

    source app_env/bin/activate

    pip install -r requirements.txt
    pip install -r requirements-dev.txt

    python manage.py makemigrations
    python manage.py migrate
    deactivate
)
