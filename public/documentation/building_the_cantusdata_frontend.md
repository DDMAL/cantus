Cantus has a build system for its client-side code which processes and combines source files to make them suitable for production environments. Currently, this system lints and minifies JavaScript resources. In the future, it may also process the CSS files and other assets. The source files it works on are contained in the directory `public/cantusdata_front_end/`. It generates files in the directories `public/cantusdata/templates/` and `public/cantusdata/static/js`.

Setup
=====

You will need to have npm installed. It can be installed using Homebrew or another package manager. Using npm, install the gulp task runner globally with the command `npm install -g gulp`.

To download the project dependencies, run the command `npm install` from the directory `public/cantusdata_front_end`. This should download everything you need to build the client-side code.

Building
========

The build system supplies the following top-level commands:

  - `gulp build`: Combine and minify the JavaScript files and build an index.html file which includes all the view templates.
  - `gulp lint`: Lint the JavaScript files.
  - `gulp`: Run both the lint and build tasks.
  - `gulp watch`: Watch for changes to the source files and lint and build incrementally as needed. (*Note*: this is still under development; currently rebuilding the JavaScript is quite slow.)
