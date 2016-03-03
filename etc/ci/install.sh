#!/bin/bash

set -ev

case "${CANTUS_CI_TEST}" in
    frontend)
        cd ./public/cantusdata/frontend
        npm install
        ;;

    server)
        # FIXME: This doesn't really belong here, but it needs to run before setup
        cp ./public/cantusdata/settings-example.py ./public/cantusdata/settings.py

        ./etc/provision/setup.sh
        ;;

    *)
        echo "Unexpected test mode: ${CANTUS_CI_TEST}"
        exit 1
        ;;
esac
