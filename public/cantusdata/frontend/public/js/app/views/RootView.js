define(["marionette"], function (Marionette)
{
    "use strict";

    /** Root view for the application, parent of all other Backbone views. */
    return Marionette.LayoutView.extend({
        el: 'body',

        regions: {
            header: '.header',
            mainContent: '#view-goes-here'
        }
    });
});