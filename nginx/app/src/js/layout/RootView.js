import Marionette from "marionette";
import Backbone from "backbone";
import Radio from "backbone.radio";

import HeaderView from "./HeaderView";
import MenuSidenavView from "./MenuSidenavView";
import SidenavView from "ui/SidenavView";

var navChannel = Radio.channel('navigation');

/** Root view for the application, parent of all other Backbone views. */
export default Marionette.View.extend({
    el: 'body',

    template: false,

    regions: {
        menuSidenav: '#menu-sidenav',
        header: '#header-container',
        mainContent: '#content-root'
    },

    initialize: function () {
        const navLinks = new Backbone.Collection(null, { sorted: false });
        this.getRegion('header').show(new HeaderView({ collection: navLinks }));
        const menuSidenavContent = new MenuSidenavView({ collection: navLinks });
        const menuSidenavView = new SidenavView({ content: menuSidenavContent });
        this.getRegion('menuSidenav').show(menuSidenavView);
        navChannel.reply('toggle:menu', () => menuSidenavView.toggle(), this);
        navChannel.reply('expand:menu', () => menuSidenavView.show(), this);
        navChannel.reply('collapse:menu', () => menuSidenavView.hide(), this);
    },

    onDestroy: function () {
        // Stop replying to all requests where `this` is the context
        navChannel.stopReplying(null, null, this);
    }
});
