#!/bin/bash

set -e

cd ./public

source app_env/bin/activate

coverage run runtests.py
