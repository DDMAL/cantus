define( ['App', 'marionette'],
    function(App, Marionette) {

        "use strict";

        /**
         * View representing a Search Result with count.
         */
        return Marionette.ItemView.extend({
            template: "#search-result-item-template",
            //tagName: '',

            /**
             * The type of search.  "all fields", "volpiano", etc.
             */
            searchField: undefined,

            showManuscriptName: true,

            modelEvents:
            {
                "change": "render"
            },

            initialize: function(options)
            {
                // FIXME(wabain): update this to use mergeOptions after updating Marionette
                this.model = options.model;
                this.searchField = options.searchField;

                if ('showManuscriptName' in options) {
                    this.showManuscriptName = options.showManuscriptName;
                }
            },

            serializeData: function()
            {
                return {
                    query: this.model.getQueryWithoutManuscript(),
                    numFound: this.model.get("numFound"),
                    searchType: this.model.getSearchType(),
                    showManuscriptName: this.showManuscriptName,
                    results: this.model.getFormattedData()
                };
            }
        });
    });
