define(['underscore', 'backbone', 'marionette'], function (_, Backbone, Marionette)
{
    'use strict';

    /**
     * Handler for the incremental loading of Solr search results.
     *
     * Its fetch method works more or less like the collection's sync method,
     * but executes multiple requests transactionally, ensuring that the collection's
     * state remains correct.
     */
    return Marionette.Object.extend({
        rows: 20,
        _fetchCount: 0,
        _currentParams: 0,

        /**
         * @param {Backbone.Collection} collection The collection to sync
         * @param {?dict} options Options for the loader. Available options:
         *   - baseUrl: a URL path to query (without query string). Can be a
         *     string or a function returning a string.
         *   - rows: The number of rows to load per request
         * @constructor
         */
        constructor: function (collection, options)
        {
            this.collection = collection;
            this.options = options;
            this.mergeOptions(['rows']);
            this._fetchCount = 0;
            this._currentParams = null;
        },

        /**
         * Fetch results from the query
         * @param {SolrQuery} solrQuery The base Solr query
         * @param {?dict} options The baseUrl can be specified as in the constructor;
         * others are used as in Backbone.Sync
         */
        fetch: function (solrQuery, options)
        {
            if (!_.has(solrQuery.params, 'rows'))
                solrQuery = solrQuery.extend({params: {rows: this.rows}});

            this._fetchCount++;

            this._currentParams = {
                fetchId: this._fetchCount,
                baseUrl: _.result(options, 'baseUrl') || _.result(this.options, 'baseUrl'),
                solrQuery: solrQuery,
                options: options,
                loaded: 0,
                numFound: null,
                fetching: false
            };

            return this._dispatchRequest({
                url: this._currentParams.baseUrl + '?' + solrQuery.toString(),
                reset: true
            });
        },

        /**
         * If an incremental load is in process and there is no pending request,
         * load more results.
         *
         * @returns {?jqXHR} The request object
         */
        continueLoading: function ()
        {
            if (!this._currentParams || this._currentParams.fetching)
                return null;

            var query = this._currentParams.solrQuery.extend({
                params: {start: this._currentParams.loaded}
            });

            var url = this._currentParams.baseUrl + '?' + query.toString();

            return this._dispatchRequest({
                url: url,
                remove: false,
                merge: false
            });
        },

        /** Invalidate the current incremental load */
        stopLoading: function ()
        {
            this._fetchCount++;
            this._currentParams = null;
        },

        /** @returns {Boolean} Return true if there are more results to load */
        hasMore: function ()
        {
            return this._currentParams !== null;
        },

        /** @returns {Number} The number of results loaded */
        loaded: function ()
        {
            return this._currentParams ? this._currentParams.loaded : this.collection.length;
        },

        /** @returns {Number} The number of results to load */
        numFound: function ()
        {
            if (this._currentParams && this._currentParams.numFound !== null)
                return this._currentParams.numFound;

            return this.collection.length;
        },

        /**
         * Dispatch a request, emulating the Backbone collection fetch logic
         * @param options
         * @private
         */
        _dispatchRequest: function (options)
        {
            this._currentParams.fetching = true;

            options = _.defaults({parse: true}, options, this._currentParams.options);
            var xhr = Backbone.sync('read', this, options);

            var _this = this;
            var fetchId = this._currentParams.fetchId;

            xhr.then(function (response)
            {
                if (_this._fetchCount !== fetchId || !_this._currentParams)
                    return;

                _this._fetchComplete(response, options);
            }, function (response)
            {
                if (options.error) options.error.call(options.context, _this.collection, response, options);
                _this.collection.trigger('error', _this.collection, response, options);
            });

            return xhr;
        },

        _fetchComplete: function (response, options)
        {
            this._currentParams.loaded += response.results.length;
            this._currentParams.fetching = false;

            if (response.numFound > this._currentParams.loaded)
            {
                this._currentParams.numFound = response.numFound;
            }
            else
            {
                this._currentParams = null;
            }

            // This is a modified version of the Backbone.Collection fetch callback code
            var success = options.success;
            var collection = this.collection;
            var method = options.reset ? 'reset' : 'set';
            collection[method](response, options);
            if (success) success(collection, response, options);
            collection.trigger('sync', collection, response, options);
        }
    });
});
