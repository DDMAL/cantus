require([
    "underscore",
    "backbone",
    "App",
    "singletons/NavigationManager",

    // Require these to ensure they are run
    "init/BackboneCustomization",
    "jquery",
    "marionette",
    "bootstrap"
], function (_, Backbone, App, NavigationManager)
{
    "use strict";

    App.on('start', function ()
    {
        var titleElem = document.getElementsByTagName('h1')[0];

        // If this is not the root page of the application, display additional
        // titling besides "Cantus Ultimus"
        if (titleElem && window.location.pathname !== '/')
            NavigationManager.registerPage({navbarTitle: titleElem.textContent});
    });

    App.start();
});