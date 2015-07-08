define(['App', 'marionette'],
function(App, Marionette)
{

"use strict";

/**
 * A chant.
 */
return Marionette.ItemView.extend({
    template: "#chant-item-template",
    tagName: 'div class="panel panel-default"',

    ui: {
        collapse: '.collapse'
    },

    events: {
        'hide.bs.collapse': 'triggerFoldChant',
        'show.bs.collapse': 'triggerUnfoldChant'
    },

    /**
     * Expose the the state of the chant to the template
     *
     * @returns {{isOpen: Function}}
     */
    templateHelpers: function ()
    {
        var self = this;

        return {
            isOpen: function ()
            {
                return self.getOption('open');
            }
        };
    },

    /**
     * Trigger a fold event when the chant is collapsed by Bootstrap
     */
    triggerFoldChant: function ()
    {
        this.trigger('fold:chant');
    },

    /**
     * Trigger a unfold event when the chant is expanded by Bootstrap
     */
    triggerUnfoldChant: function ()
    {
        this.trigger('unfold:chant');
    }
});
});