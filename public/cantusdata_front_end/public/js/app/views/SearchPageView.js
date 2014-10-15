//var CantusAbstractView = require(["views/CantusAbstractView"]);
//var SearchView = require(["views/SearchView"]);

define( ['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "views/SearchView"],
    function(App, Backbone, Marionette, $, CantusAbstractView, SearchView, template) {

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
                globalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });