define(['underscore', 'backbone', 'marionette', 'routers/WorkSpace', 'routers/RouteController'],
    function (_, Backbone, Marionette, WorkSpace, RouteController)
    {
        "use strict";

        var App = new Marionette.Application({
            behaviors: {},

            onBeforeStart: function ()
            {
                this.routeController = new RouteController();

                this.appRouter = new WorkSpace({
                    controller: this.routeController
                });

                this.routeController.onBeforeStart();
            }
        });

        App.addInitializer(function ()
        {
            Backbone.history.start({pushState: true});
        });

        return App;
    });