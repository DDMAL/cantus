require([
    "underscore",
    "backbone",
    "App",
    "routers/WorkSpace",
    "routers/RouteController",
    "behaviors/ResizeBehavior",

    // Require these to ensure they are run
    "init/BackboneCustomization",
    "jquery",
    "marionette",
    "bootstrap"
], function (_, Backbone, App, WorkSpace, RouteController, ResizeBehavior)
{
    "use strict";

    _.extend(App.behaviors, {
        resize: ResizeBehavior
    });

    App.on('before:start', function ()
    {
        this.routeController = new RouteController({
            rootView: App.rootView
        });

        this.appRouter = new WorkSpace({
            controller: this.routeController
        });

        this.routeController.triggerMethod('before:start');
    });

    App.on('start', function ()
    {
        Backbone.history.start({pushState: true});
    });

    App.start();
});
