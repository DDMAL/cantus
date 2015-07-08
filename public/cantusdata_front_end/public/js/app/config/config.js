// jscs:disable

require.config({
    baseUrl:"/static/js/app",
    // 3rd party script alias names (Easier to type "jquery" than "libs/jquery, etc")
    // probably a good idea to keep version numbers in the file names for updates checking
    paths:{
        // Core Libraries
        "jquery":"../libs/jquery",
        "jqueryui":"../libs/jqueryui",
        "jquerymobile":"../libs/jquery.mobile",
        "underscore":"../libs/underscore",
        "backbone":"../libs/backbone",
        "marionette":"../libs/backbone.marionette",
        "json2":"../libs/json2",

        // Plugins
        "backbone.validateAll":"../libs/plugins/Backbone.validateAll",
        "bootstrap":"../libs/bootstrap/bootstrap",
        "text":"../libs/plugins/text",
        "jasminejquery": "../libs/plugins/jasmine-jquery",

        // Diva
        "diva": "../libs/diva/diva",
        "diva-utils": "../libs/diva/utils",
        "diva-annotate": "../libs/diva/plugins/annotate",
        "diva-canvas": "../libs/diva/plugins/canvas",
        "diva-download": "../libs/diva/plugins/download",
        "diva-highlight": "../libs/diva/plugins/highlight",
        "diva-pagealias": "../libs/diva/plugins/pagealias"
    },
    // Sets the configuration for your third party scripts that are not AMD compatible
    shim:{
        // Twitter Bootstrap jQuery plugins
        "bootstrap":["jquery"],
        // jQueryUI
        "jqueryui":["jquery"],
        // jQuery mobile
        "jquerymobile":["jqueryui"],

        // Backbone
        "backbone":{
            // Depends on underscore/lodash and jQuery
            "deps":["underscore", "jquery"],
            // Exports the global window.Backbone object
            "exports":"Backbone"
        },
        //Marionette
        "marionette":{
            "deps":["underscore", "backbone", "jquery"],
            "exports":"Marionette"
        },
        // Backbone.validateAll plugin that depends on Backbone
        "backbone.validateAll":["backbone"],

        // Diva
        "diva": ["jquery", "diva-utils"],
        "diva-utils": ["jquery"],
        "diva-annotate": ["jquery", "diva"],
        "diva-canvas": ["jquery", "diva"],
        "diva-download": ["jquery", "diva"],
        "diva-highlight": ["jquery", "diva"],
        "diva-pagealias": ["jquery", "diva"]
    }
});