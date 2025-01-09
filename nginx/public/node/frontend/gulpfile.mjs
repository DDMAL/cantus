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

const sass = gulpSass(dartSass);

// Set path variables
var sources = {
    appJS: ['public/js/app/**/*.js', '!public/js/app/**/*.spec.js'],
    buildJS: ['./*.js'],
    templates: ['public/js/app/**/*.template.html'],
    css: ['public/css/**/*{.css,.scss}']
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
        .pipe(jscs.reporter('fail'))
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


gulp.task('bundle:css', function () {
    var sources = [
        './public/css/styles.scss',
        './public/css/diva.min.css'
    ];

    var isScssFile = /\.scss$/;
    var isCssFile = /\.css$/;
    var isDevBuild = !yargs.release;

    var compileScss = lazypipe()
        .pipe(function () {
            return sass({ loadPaths: ["node_modules"] }).on('error', sass.logError);
        })
        .pipe(autoprefixer);

    return gulp.src(sources, { base: './public/css/', sourcemaps: isDevBuild })
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
    var testEslintConfig = {
        configFile: 'public/js/.eslintrc.test.json'
    };

    return gulp.src(sources.buildJS.concat('public/js/**/*.js'))
        .pipe(gulpif((/\.spec\.js$/), eslint(testEslintConfig), eslint()))
        .pipe(eslint.format());
}

gulp.task('build', gulp.series('build:js', 'build:css'));

/*
 * High-level tasks
 */

gulp.task('default', gulp.series('lint-nofail:js', 'build', 'watch'), function (cb) {
    cb();
});