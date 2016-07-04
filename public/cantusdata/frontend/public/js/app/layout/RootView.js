import Marionette from "marionette";
import Backbone from "backbone";

import HeaderView from "./HeaderView";
import MenuSidenavView from "./MenuSidenavView";

/** Root view for the application, parent of all other Backbone views. */
export default Marionette.LayoutView.extend({
    el: 'body',

    template: false,

    regions: {
        menuSidenav: '#menu-sidenav',
        header: '#header-container',
        mainContent: '#content-root'
    },

    onRender: function ()
    {
        const navLinks = new Backbone.Collection(null, {sorted: false});

        this.menuSidenav.show(new MenuSidenavView({collection: navLinks}));
        this.header.show(new HeaderView({collection: navLinks}));
    }
});
