define(['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             CantusAbstractView,
             GlobalEventHandler)
    {

        "use strict";

        /**
         * This is the homepage of the website.
         *
         * @type {*|void}
         */
        return CantusAbstractView.extend
        ({
            el: '#view-goes-here',

            events: {
                "click #manuscripts-hero-button": function()
                {
                    Backbone.history.navigate("/manuscripts/", {trigger: true});
                }
            },

            initialize: function()
            {
                _.bindAll(this, 'render');
                this.template = _.template($('#index-template').html());
            },

            render: function()
            {
                $(this.el).html(this.template());
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });