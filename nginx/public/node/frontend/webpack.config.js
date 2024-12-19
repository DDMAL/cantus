"use strict";

var path = require('path'),
    webpack = require('webpack'),
    yargs = require('yargs').argv,
    TerserPlugin = require("terser-webpack-plugin");

module.exports = {
    optimization: {
        minimize: true,
        minimizer: [new TerserPlugin()],
    },
};;

var APP_BASE_DIR = path.resolve(__dirname, 'public/js'),
    APP_DIR = path.resolve(APP_BASE_DIR, 'app'),
    LIB_DIR = path.resolve(__dirname, 'public/node_modules'),
    TMP_DIR = path.resolve(__dirname, '.tmp');

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
        modules: [APP_DIR, LIB_DIR, TMP_DIR],

        alias: {
            marionette: 'backbone.marionette',

            // Alias the Diva path to make it easier to access the plugins, etc.
            diva: "diva.js/js/diva.js",
            bootstrap: "bootstrap/dist/js/bootstrap",
        },

    },

    module: {
        rules: [
            {
                test: /\.js$/,
                include: [APP_BASE_DIR],
                use: 'babel-loader'
            },

            {
                test: /\.template\.html$/,
                include: [APP_BASE_DIR],
                loader: 'underscore-template-loader',
                options: {
                    engine: 'underscore'
                }
            }
        ]
    },

    plugins: [
        // Inject globals that Diva relies on. While this plugin applies
        // globally, ESLint should ensure that these aren't injected in
        // app code.
        new webpack.ProvidePlugin({
            diva: 'diva',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            $: 'jquery'
        }),
    ],

    mode: 'development',
});
