#!/bin/bash

pip install poetry==1.8.2

poetry config virtualenvs.in-project true
poetry config virtualenvs.options.always-copy true
poetry config virtualenvs.options.no-pip true
poetry config virtualenvs.options.no-setuptools true

if [ $1 = "True" ]; then
    poetry install --no-cache --with debug
else
    poetry install --no-cache
fi 
