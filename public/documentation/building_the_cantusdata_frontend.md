Cantus Ultimus has a build system for its client-side code which processes and combines source files to make them suitable for production environments. Currently, this system lints and minifies JavaScript resources and client-side templates. In the future, it may also process the CSS files and other assets. The source files it works on are contained in the directory `public/cantusdata/frontend/`. It generates files in the directory `public/cantusdata/static/js`.

Setup
=====

You will need to have npm installed. It can be installed using Homebrew or another package manager. Using npm, install the gulp task runner globally with the command `npm install -g gulp`.

To download the project dependencies, run the command `npm install` from the directory `public/cantusdata/frontend`. This should download everything you need to build the client-side code.

Building
========

The build system supplies the following high-level commands:

  - `gulp`: Run the lint, build, and watch tasks.
  - `gulp build`: Combine and minify the JavaScript files and view templates.
  - `gulp lint:js`: Lint the JavaScript files.
  - `gulp watch`: Watch for changes to the source files and lint and build as needed.
