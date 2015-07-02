"use strict";

var gulp = require('gulp');
var runSequence = require('run-sequence');
var jshint = require('gulp-jshint');
var jscs = require('gulp-jscs');
var shell = require('gulp-shell');
var rename = require('gulp-rename');
var newer = require('gulp-newer');
var webpack = require('webpack');
var del = require('del');
var path = require('path');

// Set path variables
var scripts = {
    appJS: ['public/js/app/**/*.js'],
    clientJS: ['public/js/app/**/*.js', 'public/js/libs/**/*.js'],
    buildJS: ['gulpfile.js', 'webpack.config.js'],

    templates: ['public/template-assembler/templates/**/*.html']
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

gulp.task('default', ['lint-nofail:js', 'build']);
gulp.task('build', ['build:js', 'build:templates']);

/*
 * JavaScript linting
 */

gulp.task('lint:js', function ()
{
    return lintJS(scripts.appJS.concat(scripts.buildJS))
        .pipe(jshint.reporter('fail'));
});

gulp.task('lint-nofail:js', function ()
{
    return lintJS(scripts.appJS.concat(scripts.buildJS));
});

function lintJS(sources)
{
    // FIXME: this errors on jscs failure, even when we'd only
    // want it to print a warning
    return gulp.src(sources)
        .pipe(jshint({lookup: true}))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jscs());
}

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
    var dest = '../cantusdata/static/js/';

    return gulp.src(scripts.clientJS, {base: './public/js'})
        .pipe(newer(dest))
        .pipe(gulp.dest(dest));
});

gulp.task('bundle:js', function (cb)
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
    del('../cantusdata/static/js/', {force: true}, function (err)
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

// Copy templates into the Django template directory
gulp.task('build:templates', ['bundle:templates'], function ()
{
    return gulp.src('public/template-assembler/build/index.html')
        .pipe(rename('require.html'))
        .pipe(gulp.dest('../cantusdata/templates'));
});

gulp.task('bundle:templates', ['clean:templates'], shell.task([
    'python build-template.py build/'
], {
    cwd: __dirname + '/public/template-assembler/'
}));

gulp.task('clean:templates', function (done)
{
    del('../cantusdata/templates/require.html', {force: true}, function (err)
    {
        if (err)
            done(err);
        else
            done();
    });
});

gulp.task('watch', function (done)
{
    // jshint unused:false
    // Never call the callback: this runs forever

    var jsWatcher = gulp.watch(scripts.clientJS, ['lint-nofail:js', 'rebuild:js']);
    var templateWatcher = gulp.watch(scripts.templates, ['build:templates']);

    jsWatcher.on('change', logWatchedChange);
    templateWatcher.on('change', logWatchedChange);

    jsWatcher.on('change', getWatchDeletionCb('public/js', '../cantusdata/static/js'));
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
