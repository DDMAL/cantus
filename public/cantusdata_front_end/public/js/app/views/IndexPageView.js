var CantusAbstractView = require(["views/CantusAbstractView"]);

define( ['App', 'backbone', 'marionette', 'jquery', "views/CantusAbstractView"],
    function(App, Backbone, Marionette, $, CantusAbstractView, template) {

        /**
         * This is the homepage of the website.
         *
         * @type {*|void}
         */
        return CantusAbstractView.extend
        ({
            el: '#view-goes-here',

            events: {
                "click #manuscripts-hero-button" : function()
                {
                    app.navigate("/manuscripts/", {trigger: true});
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
                globalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });