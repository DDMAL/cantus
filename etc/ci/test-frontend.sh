#!/bin/bash

cd ./public/cantusdata/frontend

npm run lint
outcome=$?

npm run build

if [ $? -ne 0 ]; then
    outcome=1
fi

npm test

if [ $? -ne 0 ]; then
    outcome=1
fi

exit $outcome
