import Radio from 'backbone.radio';
import Marionette from "marionette";

import SidenavView from 'ui/SidenavView';

import MenuSidenavContentView from './MenuSidenavContentView';

import template from './menu-sidenav.template.html';

var navChannel = Radio.channel('navigation');

/**
 * View for the primary navigation menu
 */
export default Marionette.LayoutView.extend({
    template,

    regions: {
        sidenavContainer: '.sidenav-container'
    },

    onRender()
    {
        const sidenav = new SidenavView({
            content: () => new MenuSidenavContentView()
        });

        this.sidenavContainer.show(sidenav);

        // Set the context so there's an easy way to clear the bindings
        navChannel.reply('toggle:menu', () => sidenav.toggle(), this);
        navChannel.reply('expand:menu', () => sidenav.show(), this);
        navChannel.reply('collapse:menu', () => sidenav.hide(), this);
    },

    onDestroy()
    {
        // Stop replying to all requests where `this` is the context
        navChannel.stopReplying(null, null, this);
    }
});
