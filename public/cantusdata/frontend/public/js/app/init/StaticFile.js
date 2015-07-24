require([
    "underscore",
    "backbone",
    "App",

    // Require these to ensure they are run
    "init/BackboneCustomization",
    "jquery",
    "marionette",
    "bootstrap"
], function (_, Backbone, App)
{
    "use strict";

    App.start();
});