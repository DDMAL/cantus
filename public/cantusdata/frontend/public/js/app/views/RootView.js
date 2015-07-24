define([
    "marionette",
    "views/HeaderView"
], function (Marionette, HeaderView)
{
    "use strict";

    /** Root view for the application, parent of all other Backbone views. */
    return Marionette.LayoutView.extend({
        el: 'body',

        template: false,

        regions: {
            header: '.header',
            mainContent: '#view-goes-here'
        },

        onRender: function ()
        {
            this.header.show(new HeaderView());
        }
    });
});