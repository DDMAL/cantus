"use strict";

var path = require('path'),
    webpack = require('webpack'),
    yargs = require('yargs').argv;

var APP_DIR = path.resolve(__dirname, 'public/js/app'),
    LIB_DIR = path.resolve(__dirname, 'public/node_modules'),
    TMP_DIR = path.resolve(__dirname, '.tmp');

/**
 * Return the absolute path to a library file
 *
 * @param lib
 * @returns {string}
 */
function libPath(lib)
{
    return path.resolve(LIB_DIR, lib);
}

function configureBuildMode(config)
{
    if (yargs.release)
    {
        config.plugins.push(new webpack.optimize.UglifyJsPlugin({
            compress: {
                warnings: false
            }
        }));
    }
    else
    {
        config.devtool = 'cheap-module-source-map';
    }

    return config;
}

module.exports = configureBuildMode({
    context: APP_DIR,

    entry: {
        cantus: './init/Init.js'
    },

    output: {
        filename: '[name].min.js',
        path: path.resolve(__dirname, '../static/js/app'),
        publicPath: '/static/js/app/'
    },

    resolve: {
        root: [APP_DIR, LIB_DIR, TMP_DIR],

        alias: {
            marionette: 'backbone.marionette',

            // All the Diva things
            "diva": "diva.js/source/js",
            "diva-annotate": "diva.js/source/js/plugins/annotate",
            "diva-canvas": "diva.js/source/js/plugins/canvas",
            "diva-download": "diva.js/source/js/plugins/download",
            "diva-highlight": "diva.js/source/js/plugins/highlight",
            "diva-pagealias": "diva.js/source/js/plugins/pagealias"
        }
    },

    module: {
        loaders: [
            // Export the Diva global, which for mysterious
            // reasons is defined in the utils file
            {
                include: [libPath('diva.js/source/js/utils.js')],
                loader: 'exports?diva'
            },

            // Import and re-export the Diva global from the diva.js file
            {
                include: [libPath('diva.js/source/js/diva.js')],
                loaders: ['imports?diva=./utils', 'exports?diva']
            }
        ]
    },

    plugins: [
        // Inject globals that Diva relies on. While this plugin applies
        // globally, JSHint should ensure that these aren't injected in
        // app code.
        new webpack.ProvidePlugin({
            diva: 'diva',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            $: 'jquery'
        }),

        // Resolve main files which differ from the package.json entries
        new webpack.ResolverPlugin([
            // Bootstrap only has a main entry for jspm
            new webpack.ResolverPlugin.FileAppendPlugin(['/dist/js/bootstrap.js']),

            // We've aliased Diva's path so there's no main to look for
            new webpack.ResolverPlugin.FileAppendPlugin(['/diva.js'])
        ]),

        // For now we only want a single file. Since we're using AMD
        // modules, this requires explicit configuration.
        new webpack.optimize.LimitChunkCountPlugin({
            maxChunks: 1
        })
    ]
});
