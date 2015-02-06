#!/bin/sh

# Compile
grunt --force

# Assemble the templates
cd public/template-assembler/
python build-template.py
cd ../../
# Copy / paste the template
rm ../cantusdata/templates/require.html
cp public/template-assembler/build/index.html ../cantusdata/templates/require.html
echo "Copied Template"

rm -rf ../cantusdata/static/js
cp -R public/js ../cantusdata/static/js
echo "Copied JavaScript"