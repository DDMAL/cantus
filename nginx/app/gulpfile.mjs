"use strict";

import gulp from 'gulp';
import eslint from 'gulp-eslint-new';
import concat from 'gulp-concat';
import gulpSass from 'gulp-sass';
import gulpif from 'gulp-if';
import autoprefixer from 'gulp-autoprefixer';
import livereload from 'gulp-livereload';
import lazypipe from 'lazypipe';
import yargs from 'yargs';
import webpack from 'webpack';
import { deleteSync } from 'del';
import path from 'path';
import webpackConfig from './webpack.config.js';
import * as dartSass from 'sass';
import fs from 'fs';

const sass = gulpSass(dartSass);

// Set path variables
var sources = {
    appJS: ['src/js/**/*.js', '!src/js/**/*.spec.js'],
    buildJS: ['./*.js'],
    templates: ['src/js/**/*.template.html'],
    css: ['src/styles/**/*{.css,.scss}']
};

sources.clientJS = ['public/node_modules'].concat(sources.appJS).concat(sources.templates);

var getWebpackCompiler = (function () {
    var compiler = null;

    return function () {
        if (!compiler)
            compiler = webpack(webpackConfig);

        return compiler;
    };
})();

/*
 * JavaScript linting
 */

gulp.task('lint:js', function () {
    return lintJS()
        .pipe(eslint.failAfterError());
});

gulp.task('lint-nofail:js', function () {
    return lintJS();
});

/*
 * JavaScript build tasks
 */

gulp.task('bundle:js', function (cb) {
    var onBundleComplete = function (err, stats) {
        console.log(stats.toString({
            colors: true,
            hash: false,
            version: false
        }));

        if (err) {
            cb(err);
        }
        else {
            var fullStats = stats.toJson();

            // Reload changed files
            fullStats.assets.filter(function (asset) {
                return asset.emitted;
            }).map(function (asset) {
                return fullStats.publicPath + asset.name;
            }).forEach(function (path) {
                livereload.changed(path);
            });

            cb();
        }
    };

    getWebpackCompiler().run(onBundleComplete);
});

gulp.task('clean:js', function (cb) {
    deleteSync(['../static/js/', './.tmp'], { force: true }),
        cb();
});

gulp.task('rebuild:js', gulp.series('bundle:js'));

gulp.task('build:js', gulp.series('clean:js', 'bundle:js'), function (cb) {
    cb();
});

/*
 * CSS build tasks
 */


// Derive a #diva-wrapper-scoped copy of Diva v7's stylesheet from the vendored
// source at build time. Diva v7 injects this CSS globally and its
// generic class names (.modal, .status, .thumbs, ...) collide with Bootstrap/
// Cantus; v7 renders its whole UI inside #diva-wrapper, so scoping it there
// isolates it (DivaBackendV7 suppresses v7's own global injection). Generating
// from the vendored files keeps this in sync automatically on a Diva upgrade --
// there is no committed scoped copy to regenerate by hand.
var DIVA7_STYLE_DIR = './dependencies/diva.js.v7/src/styles/';
// Concatenation order matches Diva v7's own scripts/minify-css.mjs.
var DIVA7_STYLE_FILES = ['theme', 'app', 'sidebar', 'toolbar', 'modal', 'collection'];

function generateScopedDiva7Css() {
    var body = DIVA7_STYLE_FILES
        .map(function (name) {
            return fs.readFileSync(path.join(DIVA7_STYLE_DIR, name + '.css'), 'utf8');
        })
        .join('\n')
        // v7 declares its design tokens on :root; rebind them to the wrapper so
        // var(--diva-*) still resolves once everything is nested under it.
        .replace(/:root/g, '&');

    var compiled = dartSass.compileString('#diva-wrapper {\n' + body + '\n}\n').css;

    fs.mkdirSync('./.tmp', { recursive: true });
    var outPath = './.tmp/diva7-viewer.css';
    fs.writeFileSync(outPath, compiled);
    return outPath;
}

gulp.task('bundle:css', function () {
    var sources = [
        './src/styles/styles.scss',
        './dependencies/diva.js/build/diva.css',
        generateScopedDiva7Css()
    ];

    var isScssFile = /\.scss$/;
    var isCssFile = /\.css$/;
    var isDevBuild = !yargs.release;

    var compileScss = lazypipe()
        .pipe(function () {
            return sass({ loadPaths: ["node_modules"] }).on('error', sass.logError);
        })
        .pipe(autoprefixer);

    return gulp.src(sources, { base: './src/styles/', sourcemaps: isDevBuild })
        .pipe(gulpif(isScssFile, compileScss()))
        .pipe(concat('cantus-min.css'))
        .pipe(gulp.dest('../static/css', { sourcemaps: '.' }))
        .pipe(gulpif(isCssFile, livereload())); // Don't reload for sourcemaps
});

gulp.task('clean:css', function (cb) {
    deleteSync('../static/css/', { force: true });
    cb();
});

gulp.task('rebuild:css', gulp.series('bundle:css'));

gulp.task('build:css', gulp.series('clean:css', 'bundle:css'), function (cb) {
    cb();
});
/*
 * Watching
 */

gulp.task('watch', function (cb) // eslint-disable-line no-unused-vars
{
    // Never call the callback: this runs forever

    // Run the livereload server
    livereload.listen();

    var jsWatcher = gulp.watch(sources.clientJS, ['lint-nofail:js', 'rebuild:js']);
    var cssWatcher = gulp.watch(sources.css, ['rebuild:css']);

    jsWatcher.on('change', logWatchedChange);
    cssWatcher.on('change', logWatchedChange);
});

/**
 * Output a log message for a gulp.watch event
 *
 * @param ev The change event
 */
function logWatchedChange(ev) {
    console.log("File '" + path.relative('.', ev.path) + "' was " + ev.type);
}

function lintJS() {
    var lintSources = sources.buildJS.slice();

    if (fs.existsSync('public/js')) {
        lintSources.push('public/js/**/*.js');
    }

    return gulp.src(lintSources)
        .pipe(eslint({ configType: 'eslintrc' }))
        .pipe(eslint.format());
}

gulp.task('build', gulp.series('build:js', 'build:css'));

/*
 * High-level tasks
 */

gulp.task('default', gulp.series('lint-nofail:js', 'build', 'watch'), function (cb) {
    cb();
});
