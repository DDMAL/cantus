define(["marionette",
        "views/SearchView",
        "singletons/GlobalEventHandler"],
    function(Marionette,
             SearchView,
             GlobalEventHandler)
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
                    query: options.query,
                    showManuscriptName: true
                });
            },

            onRender: function()
            {
                this.searchRegion.show(this.searchView, {preventDestroy: true});
                GlobalEventHandler.trigger("renderView");
            }
        });
    });