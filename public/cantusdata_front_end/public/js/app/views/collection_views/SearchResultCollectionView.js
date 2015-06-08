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
                "sync": "render",
                "add remove reset": "updateResultListStyling"
            },

            ui: {
                resultList: '.result-list'
            },

            initialize: function()
            {
                _.bindAll(this, 'updateResultListStyling');

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

            /**
             * Hide the result table if there are no results in it
             * (it doesn't make sense to show just a header)
             */
            updateResultListStyling: function ()
            {
                if (this.collection.length === 0)
                    this.ui.resultList.hide();
                else
                    this.ui.resultList.show();
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
