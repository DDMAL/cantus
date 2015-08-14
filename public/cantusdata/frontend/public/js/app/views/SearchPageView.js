define(["marionette",
        "views/SearchView",
        "views/ChantSearchProvider"],
    function(Marionette,
             SearchView,
             ChantSearchProvider)
    {

        "use strict";

        /**
         * This page is for searching.
         *
         * @constructor
         */
        return Marionette.LayoutView.extend({
            template: '#search-page-template',

            regions: {
                searchRegion: '#search'
            },

            // Subviews
            searchView: null,

            initialize: function(options)
            {
                // Initialize the subview
                this.searchView = new SearchView({
                    providers: [new ChantSearchProvider({
                        additionalResultFields: ['manuscript', 'mode', 'genre', 'office']
                    })],
                    searchTerm: options.searchTerm
                });
            },

            onRender: function()
            {
                this.searchRegion.show(this.searchView, {preventDestroy: true});
            }
        });
    });