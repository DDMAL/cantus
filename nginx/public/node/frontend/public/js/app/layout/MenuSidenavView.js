import _ from "underscore";
import Marionette from "marionette";
import Radio from "backbone.radio";

import template from './menu-sidenav.template.html';

var navChannel = Radio.channel('navigation');

/**
 * View for the primary navigation menu
 */
export default Marionette.View.extend({
    template,

    events: {
        "click": function (event) {
            if (!event.defaultPrevented) {
                navChannel.request('collapse:menu');
            }
        }
    },

    templateContext: {
        serializeAttributes: function (attr) {
            return _.map(attr, function (val, key) {
                return key + '="' + _.escape(val) + '"';
            }).join(' ');
        }
    }
});
