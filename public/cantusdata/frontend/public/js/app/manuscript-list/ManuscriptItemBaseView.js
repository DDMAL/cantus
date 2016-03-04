import Marionette from "marionette";

import template from './manuscript-item.template.html';

/**
 * Shared base class for presenting manuscript table entries, extended
 * further for current and future manuscripts
 */
export default Marionette.ItemView.extend({
    template,
    tagName: 'tr',

    ui: {
        tooltips: '[data-toggle=tooltip]'
    },

    onRender: function ()
    {
        // Initialize tooltips
        this.ui.tooltips.tooltip();
    }
});
