define(['underscore', 'backbone', 'marionette', 'views/RootView'],
    function (_, Backbone, Marionette, RootView)
    {
        "use strict";

        var App = new Marionette.Application({
            behaviors: {},

            onBeforeStart: function ()
            {
                // Instantiate the root view
                this.rootView = new RootView();
                this.rootView.render();
            }
        });

        return App;
    });