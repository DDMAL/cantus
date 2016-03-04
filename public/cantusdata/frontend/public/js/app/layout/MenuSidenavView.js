import Radio from 'backbone.radio';
import Marionette from "marionette";

import SidenavView from 'ui/SidenavView';

import MenuSidenavContentView from './MenuSidenavContentView';

import template from './menu-sidenav.template.html';

var sidenavChannel = Radio.channel('nav-menu');

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

        sidenavChannel.reply('toggle', () => sidenav.toggle(), this);
        sidenavChannel.reply('expand', () => sidenav.show(), this);
        sidenavChannel.reply('collapse', () => sidenav.hide(), this);
    },

    onDestroy()
    {
        // Stop replying to all requests where `this` is the context
        sidenavChannel.stopReplying(null, null, this);
    }
});
