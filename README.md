# [Cantus Ultimus](http://cantus.simssa.ca/)

[![Build Status](https://travis-ci.org/DDMAL/cantus.svg?branch=develop)](https://travis-ci.org/DDMAL/cantus) [![Coverage Status](https://coveralls.io/repos/github/DDMAL/cantus/badge.svg?branch=develop)](https://coveralls.io/github/DDMAL/cantus?branch=develop)

Serving images on a website using [Apache Solr](http://lucene.apache.org/solr/), [Diva.js](https://ddmal.github.io/diva.js/) and the [CANTUS](http://cantusdatabase.org/) collection.


## Setup

Rename `gunicorn_start-example.sh` and `settings-example.py` when cloning/pulling from repo and running.

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
