import Marionette from "marionette";
import HeaderView from "views/HeaderView";
import MenuSidenavView from "views/MenuSidenavView";

/** Root view for the application, parent of all other Backbone views. */
export default Marionette.LayoutView.extend({
    el: 'body',

    template: false,

    regions: {
        menuSidenav: '#menu-sidenav',
        header: '#header-container',
        mainContent: '#view-goes-here'
    },

    onRender: function ()
    {
        this.menuSidenav.show(new MenuSidenavView());
        this.header.show(new HeaderView());
    }
});
