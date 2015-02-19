define(['jquery', 'backbone', 'marionette', 'underscore'],
    function ($, Backbone, Marionette, _) {
        "use strict";


        var App = new Backbone.Marionette.Application();

        //Organize Application into regions corresponding to DOM elements
        //Regions can contain views, Layouts, or subregions nested as necessary
//        App.addRegions({
//            headerRegion:"header",
//            mainRegion:"#main"
//        });

        App.addInitializer(function () {
            Backbone.history.start({ pushState: true });
        });

//        App.mobile = isMobile();

        return App;
    });