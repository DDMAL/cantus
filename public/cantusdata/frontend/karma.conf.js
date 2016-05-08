"use strict";

var _ = require('underscore');

module.exports = function (config)
{
    var path = require('path'),
        webpack = require('webpack'),
        generalWebpackConfig = require('./webpack.config');

    var webpackConfig = _.defaults({
        devtool: 'inline-source-map',

        plugins: generalWebpackConfig.plugins.concat([
            new webpack.optimize.LimitChunkCountPlugin({
                maxChunks: 1
            })
        ])
    }, deepClone(generalWebpackConfig));

    // Instrument code for coverage info
    webpackConfig.module.preLoaders = (webpackConfig.module.preLoaders || []).concat([
        {
            test: function (fname)
            {
                return /\.js$/.test(fname) && !/\.spec\.js/.test(fname);
            },
            include: path.resolve('public/js/app'),
            loader: 'babel-istanbul'
        }
    ]);

    // Support the "test" module
    webpackConfig.resolve.alias.test = path.resolve(__dirname, 'public/js/test');

    // Delete the entry point; this will be set dynamically
    delete webpackConfig.entry;

    config.set({
        browsers: ['PhantomJS'],
        files: ['public/js/**/*.spec.js'],
        frameworks: ['jasmine-jquery', 'jasmine-ajax', 'jasmine'],

        reporters: ['mocha', 'coverage'],

        coverageReporter: {
            instrumenters: {
                'babel-istanbul': require('babel-istanbul')
            },
            reporters: [
                { type: 'html' },
                { type: 'lcovonly', subdir: '.' },
                { type: 'text-summary' }
            ],
            dir: 'coverage/'
        },

        preprocessors: {
            'public/js/**/*.js': ['webpack', 'sourcemap']
        },

        webpack: webpackConfig,

        webpackMiddleware: {
            noInfo: true
        }
    });
};

function deepClone(obj)
{
    if (!obj || typeof obj !== 'object' || obj.__proto__ !== Object.prototype)
        return obj;

    return _.mapObject(obj, deepClone);
}
