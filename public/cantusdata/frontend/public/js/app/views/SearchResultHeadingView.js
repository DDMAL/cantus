import _ from 'underscore';
import Marionette from 'marionette';

// States for the view
// These are published statically on the view
var NO_SEARCH = 0,
    SUCCESS = 1,
    FAILURE = 2,
    LOADING = 3;

var viewError = function (message)
{
    var err = new Error(message);
    err.name = 'SearchResultHeadingViewError';
    return err;
};

/**
 * A heading for search results, synchronized to the collection state. Displays the number
 * of results, a message on errors, and optionally a spinner while requests are pending.
 *
 * Options:
 *   - `getSearchMetadata` (required): The function called to get metadata on the search.
 *     It needs to return `query` and can optionally return `fieldName` (used to build a
 *     header) and `numFound` (overriding the collection's length).
 *
 *   - `showLoading` (default false): Whether to show a loading state while the request loads
 */
export default Marionette.ItemView.extend({
    collectionEvents: {
        request: 'searchLoading',
        sync: 'searchSucceeded',
        error: 'searchFailed',
        reset: 'collectionReset'
    },

    templateMap: [
        false, // NO_SEARCH
        '#search-result-heading-template', // SUCCESS
        '#search-result-error-template', // FAILURE
        '#search-result-loading-template' // LOADING
    ],

    // Initial state
    state: NO_SEARCH,

    initialize: function ()
    {
        // FIXME(wabain): maybe debounce loading to allow a grace period instead of making it optional?
        this.showLoading = this.getOption('showLoading');

        this.getSearchMetadata = this.getOption('getSearchMetadata');

        if (!_.isFunction(this.getSearchMetadata))
        {
            throw viewError('Require a function getSearchMetadata but got ' + this.getSearchMetadata);
        }

        this.setState(this.state);
    },

    onRender: function ()
    {
        // If the template is false then we don't want to display anything
        // (no state should persist between renders)
        if (!this.currentTemplate)
            this.$el.empty();
    },

    getTemplate: function ()
    {
        return this.currentTemplate;
    },

    templateHelpers: function ()
    {
        var defaults = {
            fieldName: null,
            numFound: this.collection.length,
            errorMessage: this.error ? this.getErrorMessage(this.error) : null
        };

        if (this.metadata)
            return _.defaults(_.clone(this.metadata), defaults);

        return defaults;
    },

    searchLoading: function ()
    {
        if (this.showLoading)
        {
            this.setState(LOADING);
            this.render();
        }
    },

    searchSucceeded: function ()
    {
        this.setState(SUCCESS);
        this.render();
    },

    searchFailed: function (collection, resp)
    {
        this.setState(FAILURE, {error: resp});
        this.render();
    },

    collectionReset: function ()
    {
        this.setState(NO_SEARCH);
        this.render();
    },

    setState: function (state, parameters)
    {
        this.metadata = null;
        this.error = null;

        switch (state)
        {
            case NO_SEARCH:
                break;

            case LOADING:
            case SUCCESS:
                this.metadata = this.getSearchMetadata();
                break;

            case FAILURE:
                this.error = parameters.error;
                break;

            default:
                throw viewError('Unexpected state ' + state);
        }

        this.state = state;
        this.currentTemplate = this.templateMap[state];
    },

    getErrorMessage: function (resp)
    {
        if (resp.status >= 500)
        {
            return 'The server encountered an error';
        }

        if (_.has(resp.responseJSON, 'detail'))
        {
            return resp.responseJSON.detail;
        }

        return 'The search could not be completed';
    }
}, {
    // Expose these for testing
    states: {
        NO_SEARCH: NO_SEARCH,
        SUCCESS: SUCCESS,
        FAILURE: FAILURE,
        LOADING: LOADING
    }
});
