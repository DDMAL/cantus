var gulp = require('gulp');
var jshint = require('gulp-jshint');
var shell = require('gulp-shell');
var rename = require('gulp-rename');
var requirejs = require('requirejs');
var del = require('del');

gulp.task('default', ['lint:js', 'build:js', 'build:templates']);

/*
 * JavaScript build tasks
 */

// Copy needed files into the Django static directory
gulp.task('build:js', ['bundle:js'], function ()
{
    var filesToCopy = [
        './public/js/app/init/DesktopInit.min.js',
        './public/js/app/config/config.js',
        './public/js/libs/require.js'
    ];

    return gulp.src(filesToCopy, {base: './public/js/'})
        .pipe(gulp.dest('../cantusdata/static/js/'));
});

gulp.task('lint:js', function ()
{
    return gulp.src(['gulpfile.js', 'public/js/app/**/*.js', '!public/js/app/**/*.min.js'])
        .pipe(jshint({lookup: true}))
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail'));
});

gulp.task('bundle:js', ['clean:js'], function (done)
{
    var bundlingComplete = function ()
    {
        done();
    };

    requirejs.optimize({
        baseUrl: "public/js/app",
        wrap: true,
        // Cannot use almond since it does not currently appear to support requireJS's config-map
        name: "../libs/almond",
        preserveLicenseComments: false,
        optimize: "uglify",
        mainConfigFile: "public/js/app/config/config.js",
        include: ["init/DesktopInit"],
        out: "public/js/app/init/DesktopInit.min.js"
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
