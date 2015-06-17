define( ['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "views/SearchView",
        "views/ModalView",
        "views/TopMenuView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $, CantusAbstractView, SearchView, ModalView, TopMenuView, GlobalEventHandler) {

        /**
         * Provide an alert message to the user.
         */
        return CantusAbstractView.extend
        ({
            // Subviews
            topMenuView: null,
            searchView: null,
            searchModalView: null,

            initialize: function()
            {
                _.bindAll(this, 'render');
                this.template= _.template($('#header-template').html());
                // The search view that we will shove into the modal box
                this.searchView = new SearchView({showManuscriptName: true});
                // The modal box for the search pop-up
                this.searchModalView = new ModalView({title: "Search", view: this.searchView});
                // Create the TopMenuView with all of its options
                this.topMenuView = new TopMenuView(
                    {
                        menuItems: [
                            {
                                name: "Manuscripts",
                                url: "/manuscripts/",
                                active: false
                            },
                            {
                                name: "Search",
                                tags: 'data-toggle="modal" data-target="#myModal"',
                                url: "#",
                                active: false
                            }
                        ]
                    }
                );
            },

            render: function()
            {
                // Render the template
                $(this.el).html(this.template());
                // Render subviews
                this.assign(this.topMenuView, '#top-menu');
                this.assign(this.searchModalView, '#search-modal');
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });
