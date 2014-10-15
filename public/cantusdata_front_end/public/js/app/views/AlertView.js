//var CantusAbstractView = require(["views/CantusAbstractView"]);

define( ['App', 'backbone', 'marionette', 'jquery', "views/CantusAbstractView"],
    function(App, Backbone, Marionette, $, CantusAbstractView, template) {

        /**
         * Provide an alert message to the user.
         */
        return CantusAbstractView.extend
        ({
            alertRoles: ["success", "info", "warning", "danger"],

            role: "info",
            content: undefined,

            initialize: function(options)
            {
                _.bindAll(this, 'render');
                this.template = _.template($('#alert-template').html());
                this.role = options.role;
                this.content = options.content;
            },

            render: function()
            {
                $(this.el).html(this.template(
                    {
                        role: this.role,
                        content: this.content
                    }
                ));
                globalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });