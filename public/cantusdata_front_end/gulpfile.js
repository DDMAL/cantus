var gulp = require('gulp');
var runSequence = require('run-sequence');
var jshint = require('gulp-jshint');
var shell = require('gulp-shell');
var rename = require('gulp-rename');
var newer = require('gulp-newer');
var requirejs = require('requirejs');
var del = require('del');
var path = require('path');

// Set path variables
var scripts = {
    appJS: ['public/js/app/**/*.js'],
    clientJS: ['public/js/app/**/*.js', 'public/js/libs/**/*.js'],
    buildJS: ['gulpfile.js'],

    templates: ['public/template-assembler/templates/**/*.html']
};

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
    return gulp.src(sources)
        .pipe(jshint({lookup: true}))
        .pipe(jshint.reporter('jshint-stylish'));
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
    var bundlingComplete = function ()
    {
        cb();
    };

    requirejs.optimize({
        baseUrl: "public/js/app",
        wrap: true,
        // Cannot use almond since it does not currently appear to support requireJS's config-map
        name: "../libs/almond",
        preserveLicenseComments: false,
        optimize: "uglify2",
        generateSourceMaps: true,
        mainConfigFile: "public/js/app/config/config.js",
        include: ["init/Init"],
        out: "../cantusdata/static/js/app/cantus.min.js"
    }, bundlingComplete);
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

gulp.task('bundle:templates', ['clean:templates'], function ()
{
    // This is recommended but ugly syntax for using gulp-shell to execute
    // a single command
    return gulp.src('').pipe(shell(['python build-template.py build/'], {
        cwd: process.cwd() + '/public/template-assembler/'
    }));
});

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
    var jsWatcher = gulp.watch(scripts.clientJS, ['lint-nofail:js', 'rebuild:js']);
    var templateWatcher = gulp.watch(scripts.templates, ['build:templates']);

    jsWatcher.on('change', logWatchedChange);
    templateWatcher.on('change', logWatchedChange);

    jsWatcher.on('change', getWatchDeletionCb('public/js', '../cantusdata/static/js'));
});

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
