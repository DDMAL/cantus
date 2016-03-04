import Marionette from "marionette";

/**
 * Draw a modal box containing a particular view.
 * This view follows the visitor design pattern.
 *
 * @type {*|void}
 */
export default Marionette.LayoutView.extend({
    title: null,
    visitorView: null,

    template: '#modal-template',

    regions: {
        body: '.modal-body'
    },

    initialize: function(options)
    {
        this.title = options.title;
        this.visitorView = options.view;
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
            title: this.title
        };
    }
});
