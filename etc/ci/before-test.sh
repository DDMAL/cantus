#!/bin/bash

set -e

case "${CANTUS_CI_TEST}" in
    frontend)
        ;;

    server)
        ./etc/ci/prepare-server.sh
        ;;

    *)
        echo "Unexpected test mode: ${CANTUS_CI_TEST}"
        exit 1
        ;;
esac
