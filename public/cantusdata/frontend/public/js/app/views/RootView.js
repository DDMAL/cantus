define([
    "marionette",
    "views/HeaderView",
    "views/MenuSidenavView"
], function (Marionette, HeaderView, MenuSidenavView)
{
    "use strict";

    /** Root view for the application, parent of all other Backbone views. */
    return Marionette.LayoutView.extend({
        el: 'body',

        template: false,

        regions: {
            menuSidenav: '#menu-sidenav',
            header: '.header',
            mainContent: '#view-goes-here'
        },

        onRender: function ()
        {
            this.menuSidenav.show(new MenuSidenavView());
            this.header.show(new HeaderView());
        }
    });
});