#!/bin/bash

set -e

# Generate Coveralls JSON for the front-end code
npm --prefix=etc/client-coveralls-coverage install
node etc/client-coveralls-coverage/index.js public/cantusdata/frontend/coverage/lcov.info public > public/client-coverage.coveralls.json

cd public/
source app_env/bin/activate

# Post the server and client coverage combined
coveralls --merge client-coverage.coveralls.json
