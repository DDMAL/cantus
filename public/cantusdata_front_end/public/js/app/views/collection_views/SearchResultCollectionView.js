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

            collectionEvents: {
                "sync reset": "render",
                "add remove": "hideIfEmpty"
            },

            ui: {
                resultList: '.result-list'
            },

            initialize: function()
            {
                _.bindAll(this, 'hideIfEmpty');

                // FIXME(wabain): update this to use mergeOptions after updating Marionette
                this.searchParameters = this.getOption('searchParameters');
                this.showManuscriptName = this.getOption('showManuscriptName');
            },

            childViewOptions: function ()
            {
                return {
                    searchType: this.searchParameters.get('field'),
                    query: this.searchParameters.get('query'),
                    showManuscriptName: this.showManuscriptName
                };
            },

            onRenderTemplate: function ()
            {
                this.hideIfEmpty();
            },

            /**
             * If there is no query then hide the view. If there is a
             * query but no results then hide the result table.
             */
            hideIfEmpty: function ()
            {
                // Catch the condition where this is fired before the template has been rendered
                if (!this.$el)
                    return;

                if (!this.searchParameters.get('query'))
                {
                    this.$el.hide();
                }
                else
                {
                    this.$el.show();

                    if (this.collection.length === 0)
                        this.ui.resultList.hide();
                    else
                        this.ui.resultList.show();
                }
            },

            serializeData: function()
            {
                return {
                    query: this.searchParameters.get('query'),
                    searchType: this.searchParameters.get('field'),
                    numFound: this.collection.metadata ? this.collection.metadata.numFound : 0,
                    showManuscriptName: this.showManuscriptName
                };
            }
        });
    });
