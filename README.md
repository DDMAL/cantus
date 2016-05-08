# [Cantus Ultimus](http://cantus.simssa.ca/)

[![Build Status](https://travis-ci.org/DDMAL/cantus.svg?branch=develop)](https://travis-ci.org/DDMAL/cantus) [![Coverage Status](https://coveralls.io/repos/github/DDMAL/cantus/badge.svg?branch=develop)](https://coveralls.io/github/DDMAL/cantus?branch=develop)

Serving images on a website using [Apache Solr](http://lucene.apache.org/solr/), [Diva.js](https://ddmal.github.io/diva.js/) and the [CANTUS](http://cantusdatabase.org/) collection.


## Setup

### Server

The easiest way to set up a development environment is to set up a virtual machine using [Vagrant](https://www.vagrantup.com/). It should also be possible (with some work) to set up the development server directly in a Unix-like environment; see the [provisioning script](https://github.com/DDMAL/cantus/blob/develop/etc/provision/setup.sh) for inspiration.

With Vagrant, execute the following commands from the root directory of the repo:

```sh
# Set up the VM (this will take a while)
$ vagrant up

# SSH into the VM and start the Solr server
$ vagrant ssh
[vagrant]$ cd /vagrant/public/solr
[vagrant]$ sudo mvn jetty:run-war

# Now in a separate shell run the Django development server
$ vagrant ssh
[vagrant]$ cd /vagrant/public
# Set up site-specific Django settings
[vagrant]$ cp cantusdata/settings-example.py cantusdata/settings.py
# Activate the Python virtualenv
[vagrant]$ source app_env/bin/activate
# We can now run the server tests
[vagrant](app_env)$ ./runtests.py
# We need to run the server on 0.0.0.0 to expose it outside of the VM
[vagrant](app_env)$ python manage.py runserver 0.0.0.0:8000
```

The site should now be running on localhost:8000.

### Cantusdata client code

The global dependencies to build the client-side code are Node.js and the Gulp task runner. Install Node.js using Homebrew or a similar package manager, then install Gulp with `npm install -g gulp`.

The build system implements the following high-level commands:

```sh
$ cd public/cantusdata/frontend

# Run the lint, build, and watch tasks:
$ gulp

# These can also be run independently:
$ gulp lint:js build watch

# Run the front-end tests:
$ npm test

# Watch and run tests on source changes:
$ npm test -- --no-single-run
```

Output is generated directly in the directories `public/cantusdata/static/js` and `public/cantusdata/static/css`.

#### Client-side dependencies

Cantus Ultimus using the npm package manager both for the front-end build dependencies and for client-side dependencies. It does this using two separate npm packages: one at `public/cantusdata/frontend` for the build process and one at `public/cantusdata/frontend/public` for the client-side dependencies. Dependencies installed for the latter package are checked into version control, the rationale being that it's important to maintain precise versioning for client-side files, but not for the build dependencies, which are also considerably larger.
