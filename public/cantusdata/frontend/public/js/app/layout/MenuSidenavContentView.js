import _ from "underscore";
import Radio from 'backbone.radio';
import Marionette from "marionette";
import NavigationManager from "singletons/NavigationManager";

import contentTemplate from './menu-sidenav-content.template.html';
import itemTemplate from './menu-sidenav-item.template.html';

var sidenavChannel = Radio.channel('nav-menu');

export const SidenavContentItemView = Marionette.ItemView.extend({
    tagName: 'li',
    template: itemTemplate,

    events: {
        click: function (event)
        {
            if (!event.defaultPrevented)
            {
                sidenavChannel.request('collapse');
            }
        }
    },

    templateHelpers: {
        serializeAttributes: function (attr)
        {
            return _.map(attr, function (val, key)
            {
                return key + '="' + _.escape(val) + '"';
            }).join(' ');
        }
    }
});

const SidenavContentView = Marionette.CompositeView.extend({
    template: contentTemplate,
    childViewContainer: 'ul',

    childView: SidenavContentItemView,

    initialize: function ()
    {
        // Use the nav items sent to the navigation manager
        this.collection = NavigationManager.navItems;
    }
});

export default SidenavContentView;