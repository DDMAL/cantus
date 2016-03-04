#!/bin/bash

set -e

if [ "$#" -eq 1 ]; then
    ROOT=$1
elif [ "$#" -eq 0 ]; then
    ROOT=`pwd`
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
    # We need a version of GCC greater than 4.6.3 for pymei. 4.8 should work.
    if [[ `gcc -dumpversion` < 4.8 ]]; then
        if [[ ! `which g++-4.8` ]]; then
            echo Installing GCC v. 4.8...

            sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
            sudo apt-get update -y
            sudo apt-get install -y gcc-4.8 g++-4.8
        fi

        export CC=`which gcc-4.8`
        export CXX=`which g++-4.8`
    fi

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

