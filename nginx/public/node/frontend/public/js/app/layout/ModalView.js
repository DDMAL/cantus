import Marionette from "marionette";

import template from './modal.template.html';

/**
 * Draw a modal box containing a particular view.
 * This view follows the visitor design pattern.
 *
 * @type {*|void}
 */
export default Marionette.LayoutView.extend({
    title: null,
    visitorView: null,
    modalId: null,

    template,

    regions: {
        body: '.modal-body'
    },

    initialize: function(options)
    {
        this.title = options.title;
        this.visitorView = options.view;
        this.modalId = options.modalId;
    },

    onRender: function()
    {
        // Render out the modal template
        if (this.visitorView !== null)
        {
            this.body.show(this.visitorView, {preventDestroy: true});
        }
    },

    serializeData: function()
    {
        return {
            title: this.title,
            modalId: this.modalId
        };
    }
});
