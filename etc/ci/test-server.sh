#!/bin/bash

set -e

cd ./public

source app_env/bin/activate

./manage.py test cantusdata neumeeditor
