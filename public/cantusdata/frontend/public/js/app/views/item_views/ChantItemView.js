define(['marionette', '../ChantRecordView'],
function(Marionette, ChantRecordView)
{

"use strict";

/**
 * A panel containing chant information
 */
return Marionette.LayoutView.extend({
    template: "#chant-item-template",

    // This needs to be set as the tag because Bootstrap
    // assumes an immediate-child relationship
    tagName: 'div class="panel panel-default"',

    regions: {
        panelBody: '.panel-body'
    },

    ui: {
        collapse: '.collapse'
    },

    events: {
        'hide.bs.collapse': 'triggerFoldChant',
        'show.bs.collapse': 'triggerUnfoldChant'
    },

    onRender: function ()
    {
        this.panelBody.show(new ChantRecordView({
            model: this.model
        }));
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