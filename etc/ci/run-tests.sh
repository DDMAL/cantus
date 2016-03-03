#!/bin/bash

set -e

case "${CANTUS_CI_TEST}" in
    frontend)
        ./etc/ci/test-frontend.sh
        ;;

    server)
        ./etc/ci/test-server.sh
        ;;

    *)
        echo "Unexpected test mode: ${CANTUS_CI_TEST}"
        exit 1
        ;;
esac
