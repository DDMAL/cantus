define( ['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $, CantusAbstractView, GlobalEventHandler, template) {

        "use strict";

        /**
         * Draw a modal box containing a particular view.
         * This view follows the visitor design pattern.
         *
         * @type {*|void}
         */
        return CantusAbstractView.extend
        ({
            title: null,
            visitorView: null,

            initialize: function(options)
            {
                _.bindAll(this, 'render');
                this.template = _.template($('#modal-template').html());

                this.title = options.title;
                this.visitorView = options.view;
            },

            render: function()
            {
                // Render out the modal template
                if (this.visitorView !== null)
                {
                    $(this.el).html(this.template({title: this.title}));
                }
                // Render out the visitor
                this.assign(this.visitorView, '.modal-body');
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });