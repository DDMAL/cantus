define( ['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "views/SearchView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             CantusAbstractView,
             SearchView,
             GlobalEventHandler,
             template) {

        "use strict";

        /**
         * This page is for searching.
         *
         * @type {*|void}
         */
        return CantusAbstractView.extend
        ({
            el: '#view-goes-here',

            // Subviews
            searchView: null,

            initialize: function(options)
            {
                _.bindAll(this, 'render');
                this.template= _.template($('#search-page-template').html());
                // Initialize the subviews
                this.searchView = new SearchView(
                    {
                        query: options.query,
                        showManuscriptName: true
                    }
                );
            },

            render: function()
            {
                $(this.el).html(this.template());
                // Render subviews
                this.assign(this.searchView, '#search');
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });