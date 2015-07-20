Cantus Ultimus has a build system for its client-side code which processes and combines source files to make them suitable for production environments. Currently, this system lints and minifies JavaScript resources, precompiles client-side templates, and compiles and bundles Sass and CSS files. In the future, it may also process other assets. The source files it works on are contained in the directory `public/cantusdata/frontend/`. It generates files in the directories `public/cantusdata/static/js` and `public/cantusdata/static/css`.

Setup
=====

You will need to have npm installed. It can be installed using Homebrew or another package manager. Using npm, install the gulp task runner globally with the command `npm install -g gulp`.

To download the project dependencies, run the command `npm install` from the directory `public/cantusdata/frontend`. This should download everything you need to build the client-side code.

Building
========

The build system supplies the following high-level commands:

  - `gulp`: Run the lint, build, and watch tasks.
  - `gulp build`: Bundle and minify the JavaScript files, view templates, and CSS.
  - `gulp lint:js`: Lint the JavaScript files.
  - `gulp watch`: Watch for changes to the source files and lint and build as needed.
