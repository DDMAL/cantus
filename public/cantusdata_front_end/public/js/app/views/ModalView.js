define(["marionette",
        "singletons/GlobalEventHandler"],
    function(Marionette, GlobalEventHandler)
    {

        "use strict";

        /**
         * Draw a modal box containing a particular view.
         * This view follows the visitor design pattern.
         *
         * @type {*|void}
         */
        return Marionette.LayoutView.extend({
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

                GlobalEventHandler.trigger("renderView");
            },

            serializeData: function()
            {
                return {
                    title: this.title
                };
            }
        });
    });