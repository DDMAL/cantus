import _ from "underscore";
import Marionette from "marionette";

import SolrQuery from "utils/SolrQuery";
import IncrementalSolrLoader from "utils/IncrementalSolrLoader";

import SearchInput from "models/SearchInput";
import SearchResultCollection from "collections/SearchResultCollection";
import SuggestionCollection from "collections/SuggestionCollection";

import SearchResultHeadingView from "../SearchResultHeadingView";
import SearchInputView from "./SearchInputView";
import SuggestionCollectionView from './suggestions/SuggestionCollectionView';
import SearchResultCollectionView from "./SearchResultCollectionView";

var KNOWN_FIELDS = [
    { type: "all", "name": "All Text Fields" },
    { type: "manuscript", "name": "Manuscript" },
    { type: "volpiano", "name": "Volpiano" },
    { type: "volpiano_literal", "name": "Volpiano (Literal)" },
    { type: "mode", "name": "Mode" },
    { type: "feast", "name": "Feast" },
    { type: "genre", "name": "Genre" },
    { type: "office", "name": "Office" },
    { type: "differentia", "name": "Differentia" },
    { type: "differentiae_database", "name": "Differentiae Database" },
    { type: "cantus_id", "name": "Cantus ID" },
];

var INITIAL_LOAD_CUTOFF = 100;
var CLIENT_SIDE_SORT_LIMIT = 500;

/**
 * Provide support for searching Cantus chant information via the search interface.
 * See SearchView for a description of the contract this class fulfills.
 */
export default Marionette.Object.extend({
    description: 'Cantus Search',

    /** Search fields this class provides */
    fields: KNOWN_FIELDS.filter(function (field) {
        return field.type !== 'manuscript';
    }),

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
        "incipit",
        "differentia",
        "finalis",
        "folio",
        "differentiae_database",
        "cantus_id"
    ],

    /**
     * Initialization options:
     *
     * - `additionalResultFields`: Types of the fields to display in the
     *   search results in addition to the folio, chant name, and (if the
     *   search type is Volpiano) the chant's Volpiano
     * - `restriction`: object with field: value mappings of restrictions
     *   to apply to all queries made by the controller
     */
    initialize: function () {
        _.bindAll(this, 'search', 'setRestriction', 'getSearchMetadata');

        // Set options
        this.restrictions = this.getOption('restrictions') || {};

        // Initialize search input model
        this.searchParameters = new SearchInput();

        // Initialize search result collection
        this.collection = new SearchResultCollection();
        this.suggestionCollection = new SuggestionCollection();

        this.resultLoadingHandler = new IncrementalSolrLoader(this.collection, {
            baseUrl: this.collection.baseUrl()
        });

        // Trigger a search when the search query or field changes
        this.listenTo(this.searchParameters, 'change:query change:field', this.search);
        this.listenTo(this.searchParameters, 'change:sortBy change:reverseSort', this._handleSort);
        this.listenTo(this.collection, 'sync', this._handleSync);
    },

    onDestroy: function () {
        this.stopListening();
    },

    getSearchMetadata: function () {
        let fieldName = this.searchParameters.get('field');
        let numFound = this.collection.metadata.numFound;
        // Modify query returned by solr so it is ready for display.
        // Remove escaping backslashes from the displayed string.
        let query = this.searchParameters.get('query');
        let displayedQuery;
        switch (fieldName) {
            case "volpiano":
            case "volpiano_literal":
                displayedQuery = query.replaceAll("\\-", "-");
                break;
            case "mode":
                displayedQuery = query.join(", ");
                break;
            default:
                displayedQuery = query;
        }
        return {
            fieldName: fieldName,
            query: query,
            numFound: numFound,
            displayedQuery: displayedQuery
        };
    },

    /**
     * Set a restriction to apply to all queries made by the controller
     * @param {string} field
     * @param {string} value
     */
    setRestriction: function (field, value) {
        this.restrictions[field] = value;

        // If there is a search active then redo it
        if (this.searchParameters.get('query'))
            this.search();
    },

    onSearch: function (query) {
        // Just set the query on the model; the actual search is triggered
        // by the change event
        this.searchParameters.set('query', query);
    },

    /**
     * Take the value of the search input box and perform a search query
     * with it. This function hits the API (possibly multiple times) every
     * time it is called if the query is non-empty.
     */
    search: function () {
        var query = this.searchParameters.get('query');
        var field = this.searchParameters.get('field');

        if (!query) {
            this.resultLoadingHandler.stopLoading();
            this.collection.reset();
            return;
        }

        if (field !== 'all') {
            // FIXME(wabain): I don't think this is ever actually triggered
            // If the field is a mode then the value is already an array
            if (_.isString(query))
                query = query.split(',');
        }

        // The default sort order is defined in the SearchInput model: by
        // folio ascending. If searching by mode, we sort by Solr's scoring 
        // and then by the given sort-by parameters
        // (this gives more appropriate results when multiple 
        // modes are selected at once).
        var params = {
            sort: this.searchParameters.get('sortBy') + ' ' +
                (this.searchParameters.get('reverseSort') ? 'desc' : 'asc')
        };

        if (field === 'mode') {
            params.sort = 'score desc, ' + params.sort;
        }

        var queryBuilder = new SolrQuery({ params: params });

        this.setSearchQueryOnBuilder(queryBuilder, field, query);

        _.forEach(this.restrictions, function (value, field) {
            queryBuilder.setField(this.getSearchField(field), value);
        }, this);

        var suggestionQuery = queryBuilder.toSuggestString();
        // suggestionQuery will be null if no suggesters are defined for this search
        if (suggestionQuery)
            this.suggestionCollection.fetch({ url: this.suggestionCollection.baseUrl() + '?' + suggestionQuery });

        this.resultLoadingHandler.fetch(queryBuilder);
    },

    /**
     * Set field, value pairs in the Solr query. 
     * 
     * For non-mode searches, set the value of the field in the 
     * query to the string entered. Note (as of May 2023): Although a 
     * connector ("OR") is passed here to the queryBuilder.setField function,
     * it does not seem like any non-mode searches have multiple values.
     * Most search types pass strings, while Volpiano-type searches pass 
     * arrays to this function, but these arrays are of length 1. 
     * 
     * For mode searches, we remove the single-letter code prefix from 
     * the search terms for special modes (eg. "F, Formulaic" --> "Formulaic")
     * so that the result can be used as a phrase in the query (chant records 
     * can have "Formulaic" in their mode field but will not have "F, Formulaic").
     * Mode searches for "basic" modes (eg. "1", "2") are left as-is. We search
     * the "mode_t_hidden" field, because that field is analyzed (and tokenized)
     * by Solr to allow results to match partial strings (eg. a chant with mode
     * "4 Chant in Transposition" will match a search for "4" and "Chant in Transposition").
     * Multiple selections in a mode search are treated as disjunctions (ORs).
     *
     * @param queryBuilder
     * @param field
     * @param query
     */
    setSearchQueryOnBuilder: function (queryBuilder, field, query) {
        if (field !== 'mode') {
            queryBuilder.setField(this.getSearchField(field), query, 'OR');
            return;
        }

        let query_modified = [];
        _.forEach(query, function (value) {
            if (value.length === 1) {
                query_modified.push(value);
            } else {
                query_modified.push(`"${value.slice(3)}"`);
            }
        });
        queryBuilder.setField('mode_t_hidden', query_modified, "OR");
    },

    /**
     * Get a searchable variant of the field. String fields need
     * to be converted to text_general to be properly searchable
     * by Solr.
     *
     * @param {string} field
     * @returns {string} a searchable field
     */
    getSearchField: function (field) {
        if (_.contains(this.stringFields, field))
            return field + '_t_hidden';

        return field;
    },

    /** Display component views for the selected search field */
    display: function (field, query, regions) {
        // Restore the last query which was searched for by this field if one exists
        this.searchParameters.set({
            field: field.type,
            query: query
        });

        // Reset the suggestion collection since we are now searching for something else
        this.suggestionCollection.reset();

        // Initialize search input model
        var searchInputView = new SearchInputView({ model: this.searchParameters });
        var suggestionCollectionView = new SuggestionCollectionView({ collection: this.suggestionCollection });

        regions.searchInput.show(searchInputView);
        regions.searchSuggestions.show(suggestionCollectionView);

        regions.searchHelper.empty();

        var headingView = new SearchResultHeadingView({
            collection: this.collection,
            getSearchMetadata: this.getSearchMetadata
        });
        regions.searchResultHeading.show(headingView);

        // Get the additional result fields to display
        var specifiedAddFields = this.getOption('additionalResultFields');
        var infoFields = _.filter(KNOWN_FIELDS, function (field) {
            return _.contains(specifiedAddFields, field.type);
        });

        var resultsView = new SearchResultCollectionView({
            collection: this.collection,
            infoFields: infoFields,
            searchParameters: this.searchParameters
        });
        regions.searchResults.show(resultsView);

        this.listenTo(resultsView, 'continue:loading', this._continueLoadingResults);

        // Send information from the search input view to the suggestion collection view and vice-versa
        this.listenTo(searchInputView, 'focus:input', suggestionCollectionView.show);
        this.listenTo(searchInputView, 'blur:input', suggestionCollectionView.hide);
        this.listenTo(searchInputView, 'keydown:input', suggestionCollectionView.keyDown);
        this.listenTo(suggestionCollectionView, 'click:suggestion', searchInputView.setQuery);
    },

    /**
     * Load more search results if they are available
     *
     * @private
     */
    _continueLoadingResults: function () {
        this.resultLoadingHandler.continueLoading();
    },

    /**
     * Continue loading search results until the cutoff for initial loading is reached. After that,
     * results will only be loaded when triggered.
     *
     * @private
     */
    _handleSync: function () {
        if (this.resultLoadingHandler.hasMore() && this.resultLoadingHandler.loaded() < INITIAL_LOAD_CUTOFF)
            this.resultLoadingHandler.continueLoading();
    },

    /**
     * If a re-sort is triggered while results are loading or while there are a large number of results
     * then just go back and start loading again with the new sort criteria. Otherwise, exectute a
     * client-side sort.
     *
     * @private
     */
    _handleSort: function () {
        if (this.resultLoadingHandler.hasMore() || this.resultLoadingHandler.numFound > CLIENT_SIDE_SORT_LIMIT) {
            this.search();
        }
        else {
            // We only specify the comparator for a one-time sort; otherwise we count on results to load in
            // the correct order
            this.collection.comparator = SearchResultCollection.getComparatorFunction(this.searchParameters);
            this.collection.sort();
            this.collection.comparator = null;
        }

    }
});
