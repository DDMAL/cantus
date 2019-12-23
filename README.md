# [Cantus Ultimus](http://cantus.simssa.ca/)

[![Build Status](https://travis-ci.org/DDMAL/cantus.svg?branch=develop)](https://travis-ci.org/DDMAL/cantus) [![Coverage Status](https://coveralls.io/repos/github/DDMAL/cantus/badge.svg?branch=develop)](https://coveralls.io/github/DDMAL/cantus?branch=develop)

Serving images on a website using [Apache Solr](http://lucene.apache.org/solr/), [Diva.js](https://ddmal.github.io/diva.js/) and the [CANTUS](http://cantusdatabase.org/) collection.

## Cloning the repository

The repository of the Cantus Ultimus website has a submodule `cantus-staticpages` with the static pages of the website.

Therefore, when cloning the repository, please add the `--recursive` flag:

```
git clone https://github.com/DDMAL/cantus.git --recursive
```

An alternative option is to clone the repository as you normally would, and then get the submodule:

```
git submodule update --init
```

## Development environment setup

The easiest way to set up a development environment is to run a virtual machine using [Vagrant](https://www.vagrantup.com/). It should also be possible (with some work) to set up the development server directly in a Unix-like environment.

With Vagrant, execute the following commands from the root directory of the repo:

```sh
# Set up the VM (this will take a while)
$ vagrant up

# SSH into the VM
$ vagrant ssh

# Go to the public folder in the VM
[vagrant]$ cd public

# Activate the Python virtualenv
[vagrant]$ source app_env/bin/activate

# Run the server on 0.0.0.0 to expose it outside of the VM
[vagrant](app_env)$ python manage.py runserver 0.0.0.0:8000
```

The site should now be running on localhost:8000.
