#!/bin/bash

echo "===== Setting up django ====="
cd public
python3 -m venv app_env
source app_env/bin/activate
pip install -r requirements.txt

echo "===== Setting the django secret key ====="
if [ -z $SECRET_KEY ]
then
    echo "===== No django secret key provided, generate one ====="
    export SECRET_KEY=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 64);
fi
echo "export SECRET_KEY=${SECRET_KEY}" >> ~/.bashrc

python manage.py makemigrations
python manage.py migrate

echo "===== Build the static files ====="
cd cantusdata/frontend
npm install
gulp build --release