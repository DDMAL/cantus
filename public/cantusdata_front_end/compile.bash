#!/bin/sh

# Compile
grunt --force

rm -rf ../cantusdata/static/js

if [ "$1" = "prod" ]; then
    # We are compiling for production, so only copy minified code
    echo "Compiling minified code for production."
    # Make an empty JS dir
    mkdir -p ../cantusdata/static/js/app/init/
    mkdir ../cantusdata/static/js/app/config/
    mkdir -p ../cantusdata/static/js/libs/
    cp public/js/app/init/DesktopInit.min.js ../cantusdata/static/js/app/init/DesktopInit.min.js
    cp public/js/app/config/config.js ../cantusdata/static/js/app/config/config.js
    cp public/js/libs/require.js ../cantusdata/static/js/libs/require.js
    # Copy just the minified site
else
    # Not production, so copy unminified code.
    cp -R public/js ../cantusdata/static/js
fi

# Assemble the templates
cd public/template-assembler/
python build-template.py build/
cd ../../
# Copy / paste the template
rm ../cantusdata/templates/require.html
cp public/template-assembler/build/index.html ../cantusdata/templates/require.html
echo "Copied Template"

echo "Copied JavaScript"