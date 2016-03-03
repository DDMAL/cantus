import Marionette from 'marionette';
import ChantRecordView from '../ChantRecordView';

/**
 * A panel containing chant information
 */
export default Marionette.LayoutView.extend({
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
        'hide.bs.collapse': '_triggerFoldChant',
        'show.bs.collapse': '_triggerUnfoldChant'
    },

    collapseContent: function ()
    {
        this.ui.collapse.collapse('hide');
    },

    expandContent: function ()
    {
        this.ui.collapse.collapse('show');
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
    _triggerFoldChant: function ()
    {
        this.trigger('fold:chant');
    },

    /**
     * Trigger a unfold event when the chant is expanded by Bootstrap
     */
    _triggerUnfoldChant: function ()
    {
        this.trigger('unfold:chant');
    }
});
