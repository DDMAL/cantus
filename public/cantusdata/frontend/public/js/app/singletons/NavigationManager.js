define(["backbone", "marionette"], function (Backbone, Marionette)
{
    "use strict";

    /**
     * Manager for navigational things
     * TODO(wabain): work out whether having this as a separate class make sense,
     * or whether it could be an attribute of the app or something */
    var NavigationManagerClass = Marionette.Object.extend({
        initialize: function ()
        {
            this.navItems = new Backbone.Collection(null, {sorted: false});
        }
    });

    return new NavigationManagerClass();
});
