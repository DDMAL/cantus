//var CantusAbstractView = require(["views/CantusAbstractView"]);

define(['App', 'backbone', 'marionette', 'jquery', "views/CantusAbstractView", "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $, CantusAbstractView, GlobalEventHandler)
    {

        return CantusAbstractView.extend
        ({
            activeButton: 0,

            initialize: function(options)
            {
                _.bindAll(this, 'render', 'registerClickEvents', "buttonClickCallback");
                this.template = _.template($('#top-menu-template').html());
                // Menu list items provided
                this.items = options.menuItems;
                this.registerClickEvents();
            },

            /**
             * Whenever a menu item is clicked, we want to push the state
             */
            registerClickEvents: function()
            {
                // Clear out the events
                this.events = {};
                // Menu items
                for (var i = 0; i < this.items.length; i++)
                {
                    this.events["click #top-menu-button-" + i] = "buttonClickCallback";
                }
                // Delegate the new events
                this.delegateEvents();
            },

            buttonClickCallback: function(event)
            {
                // If for some reason backbone history hasn't been initialized then just return
                if (!Backbone.history.started)
                    return;

                // Stop the page from auto-reloading
                event.preventDefault();
                // Figure out which button was pressed
                var buttonName = String(event.currentTarget.id);
                var id = buttonName.split('-')[buttonName.split('-').length - 1];
                // Now that we have that id, route the application to it's URL!
                var newUrl = this.items[id].url;
                var oldUrl = Backbone.history.fragment;
                // Only route to the new URL if it really is a new url!
                if (!(newUrl === "#" || newUrl.trim('/') === oldUrl.trim('/')))
                {
                    Backbone.history.navigate(this.items[id].url, {trigger: true});
                    this.setActiveButton(id);
                }
            },

            /**
             * Set which menu button is active at the moment.
             *
             * @param index
             */
            setActiveButton: function(index)
            {
                if (index === this.activeButton)
                {
                    return;
                }
                this.items[this.activeButton].active = false;
                this.activeButton = index;
                this.items[this.activeButton].active = true;
                this.render();
            },

            render: function()
            {
                $(this.el).html(this.template({items: this.items}));
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });