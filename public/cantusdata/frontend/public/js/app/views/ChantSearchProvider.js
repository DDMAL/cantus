define([
    "underscore",
    "marionette",
    "utils/SolrQuery",
    "models/SearchInput",
    "collections/SearchResultCollection",
    "views/SearchInputView",
    "views/collection_views/SearchResultCollectionView",
    "views/SearchResultHeadingView"
], function (
    _,
    Marionette,
    SolrQuery,
    SearchInput,
    SearchResultCollection,
    SearchInputView,
    SearchResultCollectionView,
    SearchResultHeadingView)
{
    "use strict";

    /**
     * Provide support for searching Cantus chant information via the search interface.
     * See SearchView for a description of the contract this class fulfills.
     */
    return Marionette.Object.extend({
        description: 'Chant search',

        showManuscriptName: true,

        /** Search fields this class provides */
        fields: [
            {type: "all", "name": "All Text Fields"},
            {type: "volpiano", "name": "Volpiano"},
            {type: "mode", "name": "Mode"},
            {type: "feast", "name": "Feast"},
            {type: "genre", "name": "Genre"},
            {type: "office", "name": "Office"}
        ],

        // Fields which are indexed in Solr as strings.
        // We need to get text_general variants of these
        // for search. (Note that we don't actually search
        // by all of these at the moment.)
        stringFields: [
            "feast",
            "office",
            "genre",
            "position",
            "mode",
            "differentia",
            "finalis",
            "folio"
        ],

        /**
         * Initialization options:
         *
         * - `showManuscriptName`: Whether to include the manuscript name as
         *   a field in the search (FIXME: at the moment, this also controls
         *   whether some other fields are displayed in the search results table)
         * - `restriction`: object with field: value mappings of restrictions
         *   to apply to all queries made by the controller
         */
        initialize: function()
        {
            _.bindAll(this, 'search', 'setRestriction', 'getSearchMetadata');

            // Mapping if queries per field
            this.cachedQueries = {};

            // Set options
            this.restrictions = this.getOption('restrictions') || {};
            this.showManuscriptName = this.getOption('showManuscriptName');

            // Initialize search input model
            this.searchParameters = new SearchInput();

            // Initialize search result collection which is sorted
            // by the criteria specified by the search input
            this.collection = new SearchResultCollection(null, {
                comparisonParameters: this.searchParameters
            });

            // Trigger a search when the search query or field changes
            this.listenTo(this.searchParameters, 'change:query change:field', this.search);
        },

        onDestroy: function ()
        {
            this.stopListening();
        },

        getSearchMetadata: function ()
        {
            // Don't present a field name
            return {
                field: null,
                query: this.searchParameters.get('query'),
                numFound: this.collection.metadata.numFound
            };
        },

        /**
         * Set a restriction to apply to all queries made by the controller
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

            this.cachedQueries[field] = query;

            if (!query)
            {
                this.collection.invalidateFetch();
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

            this.setSearchQueryOnBuilder(queryBuilder, field, query);

            _.forEach(this.restrictions, function (value, field)
            {
                queryBuilder.setField(this.getSearchField(field), value);
            }, this);

            this.collection.fetch({baseSolrQuery: queryBuilder});
        },

        /**
         * FIXME(wabain)
         *
         * This is an overly complicated workaround to push single-character
         * mode searches into a field that will return results for them.
         *
         * The problem is that currently the mode_t_hidden field doesn't
         * index single characters
         *
         * @param queryBuilder
         * @param field
         * @param query
         */
        setSearchQueryOnBuilder: function (queryBuilder, field, query)
        {
            if (field !== 'mode')
            {
                queryBuilder.setField(this.getSearchField(field), query, 'OR');
                return;
            }

            if (_.isString(query))
            {
                queryBuilder.setField(
                    query.length === 1 ? 'mode' : 'mode_t_hidden',
                    query);
                return;
            }

            var modeStringValues = [];
            var modeTextValues = [];

            _.forEach(query, function (value)
            {
                if (value.length === 1)
                    modeStringValues.push(value);
                else
                    modeTextValues.push(value);
            });

            if (modeStringValues.length === 0)
                queryBuilder.setField('mode_t_hidden', modeTextValues, 'OR');
            else if (modeTextValues.length === 0)
                queryBuilder.setField('mode', modeStringValues, 'OR');
            else
            {
                var hardCodedQuery = '(mode:(' +
                    modeStringValues.join(' OR ') +
                    ') OR mode_t_hidden:(' +
                    modeTextValues.join(' OR ') +
                    '))';

                queryBuilder.setField('_hardcodedSpecialQuery', hardCodedQuery);
            }
        },

        /**
         * Get a searchable variant of the field. String fields need
         * to be converted to text_general to be properly searchable
         * by Solr.
         *
         * @param {string} field
         * @returns {string} a searchable field
         */
        getSearchField: function (field)
        {
            if (_.contains(this.stringFields, field))
                return field + '_t_hidden';

            return field;
        },

        /** Display component views for the selected search field */
        display: function (field, regions)
        {
            // Restore the last query which was searched for by this field if one exists
            this.searchParameters.set({
                field: field.type,
                query: this.cachedQueries[field.type] || ''
            });

            regions.searchInput.show(new SearchInputView({model: this.searchParameters}));

            regions.searchHelper.empty();

            regions.searchResultHeading.show(new SearchResultHeadingView({
                collection: this.collection,
                getSearchMetadata: this.getSearchMetadata
            }));

            regions.searchResults.show(new SearchResultCollectionView({
                collection: this.collection,
                showManuscriptName: this.showManuscriptName,
                searchParameters: this.searchParameters
            }));
        }
    });
});
