"use strict";

var gulp = require('gulp');
var runSequence = require('run-sequence');
var jshint = require('gulp-jshint');
var jscs = require('gulp-jscs');
var newer = require('gulp-newer');
var concat = require('gulp-concat');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var gulpif = require('gulp-if');

var _ = require('underscore');
var lazypipe = require('lazypipe');
var yargs = require('yargs').argv;
var webpack = require('webpack');
var del = require('del');
var path = require('path');

var bundleTemplates = require('./bundle-templates').bundle;

// Set path variables
var sources = {
    appJS: ['public/js/app/**/*.js'],
    clientJS: ['public/js/app/**/*.js', 'public/js/libs/**/*.js'],
    buildJS: ['./*.js'],
    templates: ['public/templates/**/*.html'],
    css: ['public/css/**/*{.css,.scss}']
};

var getWebpackCompiler = (function ()
{
    var compiler = null;

    return function ()
    {
        if (!compiler)
            compiler = webpack(require('./webpack.config'));

        return compiler;
    };
})();

/*
 * High-level tasks
 */

gulp.task('default', function (cb)
{
    runSequence(['lint-nofail:js', 'build'], 'watch', cb);
});

gulp.task('build', ['build:js', 'build:css']);

/*
 * JavaScript linting
 */

gulp.task('lint:js', function ()
{
    return lintJS(sources.appJS.concat(sources.buildJS))
        .pipe(jshint.reporter('fail'));
});

gulp.task('lint-nofail:js', function ()
{
    return lintJS(sources.appJS.concat(sources.buildJS));
});

/*
 * JavaScript build tasks
 */

gulp.task('build:js', function (cb)
{
    runSequence(
        'clean:js',
        ['copySources:js', 'bundle:js'],
        cb
    );
});

gulp.task('rebuild:js', ['copySources:js', 'bundle:js']);

/** Copy needed files into the Django static directory */
gulp.task('copySources:js', function ()
{
    return copySources(sources.clientJS, './public/js', '../static/js');
});

gulp.task('bundle:js', ['bundle:templates'], function (cb)
{
    var onBundleComplete = function (err, stats)
    {
        console.log(stats.toString({
            colors: true,
            hash: false,
            version: false
        }));

        if (err)
            cb(err);
        else
            cb();
    };

    getWebpackCompiler().run(onBundleComplete);
});

gulp.task('clean:js', function (done)
{
    del(['../static/js/', './.tmp'], {force: true}, function (err)
    {
        if (err)
            done(err);
        else
            done();
    });
});

/*
 * Template build tasks
 */

gulp.task('bundle:templates', function ()
{
    return bundleTemplates('public/templates', '.tmp/templates.js', {
        preface: '_ = require("underscore");'
    });
});

/*
 * CSS build tasks
 */

gulp.task('build:css', function (done)
{
    runSequence(
        'clean:css',
        ['copySources:css', 'bundle:css'],
        done
    );
});

gulp.task('rebuild:css', ['copySources:css', 'bundle:css']);

gulp.task('bundle:css', function ()
{
    var sources = [
        './public/css/bootstrap-theme.min.css',
        './public/css/diva.min.css',
        './public/css/styles.scss'
    ];

    var isScssFile = _.constant((/\.scss$/));

    var compileScss = lazypipe()
        .pipe(function ()
        {
            return sass({outputStyle: 'compressed'}).on('error', sass.logError);
        });

    return gulp.src(sources, {base: './public/css/'})
        .pipe(sourcemaps.init())
        .pipe(gulpif(isScssFile, compileScss()))
        .pipe(concat('cantus.min.css'))
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest('../static/css'));
});

gulp.task('copySources:css', function ()
{
    return copySources(sources.css, './public/css', '../static/css');
});

gulp.task('clean:css', function (done)
{
    del('../static/css/', {force: true}, function (err)
    {
        if (err)
            done(err);
        else
            done();
    });
});

/*
 * Watching
 */

gulp.task('watch', function (done)
{
    // jshint unused:false
    // Never call the callback: this runs forever

    var jsWatcher = gulp.watch(sources.clientJS.concat(sources.templates), ['lint-nofail:js', 'rebuild:js']);
    var cssWatcher = gulp.watch(sources.css, ['rebuild:css']);

    jsWatcher.on('change', logWatchedChange);
    jsWatcher.on('change', getWatchDeletionCb('public/js', '../static/js'));

    cssWatcher.on('change', logWatchedChange);
    jsWatcher.on('change', getWatchDeletionCb('public/css', '../static/css'));
});

/**
 * Output a log message for a gulp.watch event
 *
 * @param ev The change event
 */
function logWatchedChange(ev)
{
    console.log("File '" + path.relative('.', ev.path) + "' was " + ev.type);
}

/**
 * Return a gulp.watch callback function which deletes a file in the
 * destination directory when they are deleted in the source directory.
 *
 * @param srcRoot
 * @param destRoot
 * @returns {Function}
 */
function getWatchDeletionCb(srcRoot, destRoot)
{
    return function (ev)
    {
        if (ev.type === 'deleted')
        {
            var destPath = path.resolve(destRoot, path.relative(srcRoot, ev.path));

            console.log("Deleting file '" + destPath + "'");
            del.sync(destPath, {force: true});
        }
    };
}

function lintJS(sources)
{
    // FIXME: this errors on jscs failure, even when we'd only
    // want it to print a warning
    return gulp.src(sources)
        .pipe(jshint({lookup: true}))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jscs());
}

function copySources(files, baseDir, dest)
{
    // Make this a no-op when doing a release build
    if (yargs.release)
        files = [];

    return gulp.src(files, {base: baseDir})
        .pipe(newer(dest))
        .pipe(gulp.dest(dest));

}