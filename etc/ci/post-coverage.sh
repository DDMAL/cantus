#!/bin/bash

set -e

case "${CANTUS_CI_TEST}" in
    frontend)
        echo TODO
        ;;

    server)
        cd public/
        source app_env/bin/activate
        coveralls
        ;;

    *)
        echo "Unexpected test mode: ${CANTUS_CI_TEST}"
        exit 1
        ;;
esac
