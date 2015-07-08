define(['jquery', 'backbone', 'marionette'],
    function ($, Backbone, Marionette)
    {
        "use strict";

        // jscs:disable validateIndentation
        var App = new Marionette.Application();

        //Organize Application into regions corresponding to DOM elements
        //Regions can contain views, Layouts, or subregions nested as necessary
//        App.addRegions({
//            headerRegion:"header",
//            mainRegion:"#main"
//        });

        App.addInitializer(function ()
        {
            Backbone.history.start({pushState: true});
        });

//        App.mobile = isMobile();

        // jscs:enable

        return App;
    });