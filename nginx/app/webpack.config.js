"use strict";

var path = require('path'),
    webpack = require('webpack'),
    yargs = require('yargs').argv;

var APP_DIR = path.resolve(__dirname, 'src/js');

function configureBuildMode(config) {
    if (yargs.release) {
        config.mode = 'production';
    }
    else {
        config.devtool = 'cheap-module-source-map';
    }

    return config;
}

module.exports = configureBuildMode({
    context: APP_DIR,

    entry: {
        cantus: './init/Init.js',
        'cantus-static': './init/StaticFile.js'
    },

    output: {
        filename: '[name]-min.js',
        chunkFilename: 'cantus.chunk.[id].min.js',
        path: path.resolve(__dirname, '../static/js/app'),
        publicPath: '/static/js/app/'
    },

    resolve: {
        modules: [APP_DIR, 'node_modules'],
        alias: {
            marionette: 'backbone.marionette',
            // Alias diva and link-watcher so that webpack looks in the
            // `dependencies` directory for them.
            diva: path.resolve(__dirname, "dependencies/diva.js/js/diva.js"),
            'link-watcher': path.resolve(__dirname, "dependencies/link-watcher/dist/link-watcher.js"),
        },

    },

    module: {
        rules: [
            {
                test: /\.js$/,
                include: [APP_DIR],
                use: {
                    loader: 'babel-loader',
                    options: {
                        targets: [
                            "> 1%",
                            "last 2 versions",
                            "Firefox ESR",
                            "Opera 12.1",
                            "ie >= 9"
                        ],
                        presets: ['@babel/preset-env']
                    }
                }
            },

            {
                test: /\.template\.html$/,
                include: [APP_DIR],
                loader: 'underscore-template-loader',
                options: {
                    engine: 'underscore'
                }
            }
        ]
    },

    plugins: [
        new webpack.ProvidePlugin({
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            $: 'jquery'
        }),
    ],

    mode: 'development',
});
