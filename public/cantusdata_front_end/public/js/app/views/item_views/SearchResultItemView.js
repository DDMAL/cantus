define( ['App', 'marionette'],
    function(App, Marionette) {

        "use strict";

        /**
         * View representing a Search Result with count.
         */
        return Marionette.ItemView.extend({
            template: "#search-result-item-template",
            tagName: 'table class="table table-striped"',

            /**
             * The type of search.  "all fields", "volpiano", etc.
             */
            searchField: undefined,

            showManuscriptName: false,

            modelEvents:
            {
                "change": "render"
            },

            initialize: function(model, searchField)
            {
                this.model = model;
                this.searchField = searchField;
            },

            serializeData: function()
            {
                return {
                    query: this.model.getQueryWithoutManuscript(),
                    numFound: this.model.get("numFound"),
                    searchType: this.searchField,
                    showManuscriptName: this.showManuscriptName,
                    results: this.model.getFormattedData()
                };
            }
        });
    });
