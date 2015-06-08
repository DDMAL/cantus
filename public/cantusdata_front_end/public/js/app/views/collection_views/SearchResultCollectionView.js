define( ['App', 'marionette', 'views/item_views/SearchResultItemView'],
    function(App, Marionette, SearchResultItemView) {

        "use strict";

        // TODO(wabain): this is misnamed since it's actually a CompositeView
        // but it should really be merged into the SearchResultView

        /**
         * View representing a Search Result with count.
         */
        return Marionette.CompositeView.extend({
            template: "#search-result-list-template",

            childView: SearchResultItemView,
            childViewContainer: '.child-container',

            showManuscriptName: true,

            /**
             * The type of search.  "all", "volpiano", etc.
             */
            searchField: null,

            // Re-render even if hypothetically no items were added or removed, since metadata could change
            collectionEvents: {
                "sync": "render"
            },

            initialize: function()
            {
                // FIXME(wabain): update this to use mergeOptions after updating Marionette
                this.searchField = this.getOption('searchField');
                this.showManuscriptName = this.getOption('showManuscriptName');
            },

            childViewOptions: function ()
            {
                return {
                    searchField: this.searchField,
                    showManuscriptName: this.showManuscriptName
                };
            },

            serializeData: function()
            {
                return {
                    query: this.collection.getQueryWithoutManuscript(),
                    numFound: this.collection.metadata ? this.collection.metadata.numFound : 0,
                    searchType: this.collection.getSearchType(),
                    showManuscriptName: this.showManuscriptName
                };
            }
        });
    });
