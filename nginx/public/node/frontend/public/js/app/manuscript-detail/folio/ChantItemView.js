import Marionette from 'marionette';
import Radio from 'backbone.radio';
import ChantRecordView from './ChantRecordView';

import template from './chant-item.template.html';

var manuscriptChannel = Radio.channel('manuscript');

/**
 * A panel containing chant information
 */
export default Marionette.View.extend({
    template,

    regions: {
        panelBody: '.accordion-body'
    },

    ui: {
        collapse: '.collapse',
        panelHeading: '.accordion-header'
    },

    events: {
        'hide.bs.collapse': '_triggerFoldChant',
        'show.bs.collapse': '_triggerUnfoldChant',
        'click @ui.panelHeading': 'onChantAccordionClick'
    },

    collapseContent: function () {
        this.ui.collapse.collapse('hide');
    },

    expandContent: function () {
        this.ui.collapse.collapse('show');
    },

    onRender: function () {
        this.getRegion('panelBody').show(new ChantRecordView({
            model: this.model
        }));
    },

    /**
     * Expose the the state of the chant to the template
     *
     * @returns {{isOpen: Function}}
     */
    templateContext: function () {
        var self = this;

        return {
            isOpen: function () {
                return self.getOption('open');
            }
        };
    },

    /**
     * Trigger a fold event when the chant is collapsed by Bootstrap
     */
    _triggerFoldChant: function () {
        this.trigger('fold:chant');
    },

    /**
     * Trigger a unfold event when the chant is expanded by Bootstrap
     */
    _triggerUnfoldChant: function () {
        this.trigger('unfold:chant');
    },

    /**
     * Trigger an event to stop any audio that is playing
        */
    onChantAccordionClick: function () {
        manuscriptChannel.trigger('chantAccordion:click');
    }
});
