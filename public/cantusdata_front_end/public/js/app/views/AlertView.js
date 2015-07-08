define(['jquery',
        "views/CantusAbstractView",
        "singletons/GlobalEventHandler"],
    function($,
             CantusAbstractView,
             GlobalEventHandler)
    {

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
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });