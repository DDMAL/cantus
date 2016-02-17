#!/bin/bash

set -e

if [ "$#" -eq 1 ]; then
    ROOT=$1
elif [ "$#" -eq 0 ]; then
    ROOT=.
else
    echo "Usage: $0 [root_path]"
    exit 1
fi


echo "==================== INSTALLING LIBMEI ===================="

sudo apt-get install -y git cmake uuid-dev libboost-python-dev

if [ ! -d libmei ]; then
    git clone "https://github.com/DDMAL/libmei.git" --branch v2.0.0 libmei
fi

(
    cd libmei

    mkdir -p build; cd build
    cmake ..
    make
    sudo make install

    cd ../python

    issue_url=https://github.com/DDMAL/libmei/issues/81

    # Patch setup.py to fix an issue with Boost dependency naming
    # * https://github.com/DDMAL/libmei/wiki/Installing-the-Python-bindings
    # * https://github.com/DDMAL/libmei/issues/81
    if git apply --check "$ROOT/etc/provision/pymei-setup-fix.patch"; then
        echo "Applying patch for $issue_url"
        git apply "$ROOT/etc/provision/pymei-setup-fix.patch"
    else
        echo "Skipping patch for $issue_url"
        echo "(The patch may already be applied)"
    fi

    source "$ROOT/public/app_env/bin/activate"
    python setup.py build
    python setup.py install
)

