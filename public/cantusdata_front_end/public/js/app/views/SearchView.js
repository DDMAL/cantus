define(['backbone', 'marionette',
        "utils/SolrQuery",
        "models/SearchInput",
        "collections/SearchResultCollection",
        "views/collection_views/SearchResultCollectionView",
        "views/SearchInputView"],
    function(Backbone, Marionette,
             SolrQuery,
             SearchInput,
             SearchResultCollection,
             SearchResultCollectionView,
             SearchInputView) {

        "use strict";

        /**
         * Top-level search view
         */
        return Marionette.LayoutView.extend({
            template: "#search-template",

            showManuscriptName: true,

            regions: {
                searchResultRegion: ".search-results",
                searchInputRegion: ".search-input-container"
            },

            /**
             * Initialization options:
             *
             * - `restriction`: restrictions to apply to all queries originating
             *    from the view
             * - `query`: initial query to search for
             * - `field`: initial field to search with
             */
            initialize: function()
            {
                _.bindAll(this, 'search', 'setRestriction');

                // Set options
                this.restrictions = this.getOption('restrictions') || {};
                this.showManuscriptName = this.getOption('showManuscriptName');

                // Initialize search result collection
                this.collection = new SearchResultCollection();

                // Initialize search input model
                this.searchParameters = new SearchInput();

                this.listenTo(this.searchParameters, 'change', this.search);

                if (this.getOption('query'))
                    this.searchParameters.set('query', this.getOption('query'));

                if (this.getOption('field'))
                    this.searchParameters.set('field', this.getOption('field'));
            },

            /**
             * Add a restriction to apply to all queries originating in the view.
             * @param {string} field
             * @param {string} value
             */
            setRestriction: function (field, value)
            {
                this.restrictions[field] = value;

                // If there is a search active then redo it
                if (this.searchParameters.get('query'))
                    this.search();
            },

            /**
             * Take the value of the search input box and perform a search query
             * with it. This function hits the API (possibly multiple times) every
             * time it is called if the query is non-empty.
             */
            search: function()
            {
                var query = this.searchParameters.get('query');
                var field = this.searchParameters.get('field');

                if (!query)
                {
                    this.collection.reset();
                    return;
                }

                if (field !== 'all')
                {
                    // FIXME(wabain): I don't think this is ever actually triggered
                    // If the field is a mode then the value is already an array
                    if (_.isString(query))
                        query = query.split(',');
                }

                var queryBuilder = new SolrQuery();
                queryBuilder.setField(field, query, 'OR');

                _.forEach(this.restrictions, function (value, field) {
                    queryBuilder.setField(field, value);
                });

                this.collection.fetch({baseSolrQuery: queryBuilder});
            },

            onRender: function ()
            {
                this.searchInputRegion.show(new SearchInputView({model: this.searchParameters}));

                this.searchResultRegion.show(new SearchResultCollectionView({
                    collection: this.collection,
                    showManuscriptName: this.showManuscriptName,
                    searchParameters: this.searchParameters
                }));
            }
        });
    });