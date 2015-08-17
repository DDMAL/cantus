define(["underscore", "backbone", "marionette"], function (_, Backbone, Marionette)
{
    "use strict";

    /** Manager for navigational state. Holds the collection of nav links and the page title. */
    var NavigationManagerClass = Marionette.Object.extend({
        initialize: function ()
        {
            this.navItems = new Backbone.Collection(null, {sorted: false});

            this.titling = new Backbone.Model({
                defaults: {
                    title: null,
                    navbarTitle: null
                }
            });
        },

        registerPage: function (options)
        {
            var titleSettings = _.defaults(options, {title: null});

            if (titleSettings.navbarTitle === undefined)
                titleSettings.navbarTitle = titleSettings.title;

            this.titling.set(titleSettings);
        }
    });

    return new NavigationManagerClass();
});
