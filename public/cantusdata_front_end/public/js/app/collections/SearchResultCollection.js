define(["underscore", "backbone", "models/SearchResult", "config/GlobalVars"],
    function(_, Backbone, SearchResult, GlobalVars)
    {

        "use strict";

        /**
         * Comparison utility function. Return 0 for equal values, -1 if a is less than b,
         * and 1 otherwise.
         *
         * @param {*} a
         * @param {*} b
         * @returns {number}
         */
        function cmp(a, b)
        {
            // Use weak equality because less-than uses weak semantics as well.
            // Ideally values should be of the same type, however.
            if (a == b)
                return 0;

            return a < b ? -1 : 1;
        }

        return Backbone.Collection.extend({
            // Sometimes overridden
            // TODO(wabain): find out what would override this and why
            searchPage: "search/",

            model: SearchResult,

            initialize: function(models, options)
            {
                this._fetchCount = 0;

                var params = options && options.comparisonParameters;

                if (params)
                    this.useComparisonParameters(params);
            },

            /**
             * Set this collection to sort its models by the parameters
             * specified by the comparison model, re-sorting when those
             * parameters change.
             *
             * Specifically, it looks for the following attributes:
             *
             *  - `sortBy` (string): the field to sort by
             *  - `reverseSort` (boolean): whether to reverse the sort order
             *
             * @param comparisonModel
             */
            useComparisonParameters: function(comparisonModel)
            {
                this.comparisonParameters = comparisonModel;

                this.comparator = function (itemA, itemB)
                {
                    var fieldName = comparisonModel.get('sortBy');
                    var reversed = comparisonModel.get('reverseSort');

                    var compared = cmp(itemA.get(fieldName), itemB.get(fieldName));

                    if (compared === 0)
                    {
                        // Use item_id as a fallback field to keep sorting stable

                        // FIXME(wabain): there are probably better fallback choices if the type
                        // of result is given. For instance, chant order. How should I handle this?

                        compared = cmp(itemA.get('item_id'), itemB.get('item_id'));
                    }

                    return reversed ? -compared : compared;
                };

                // Re-sort when the comparison values change
                this.listenTo(comparisonModel, 'change:sortBy change:reverseSort', this.sort);

                // Perform an initial re-sort
                this.sort();
            },

            /**
             * Return the composed base URL
             *
             * @returns {string}
             */
            baseUrl: function ()
            {
                return GlobalVars.siteUrl + this.searchPage;
            },

            /**
             * Store the full response as metadata, but keep the response as
             * the collection value.
             *
             * @param response
             * @returns {*}
             */
            parse: function (response)
            {
                // TODO: move metadata into a model. That model could do the fetch and then
                // this collection would be populated subsequently.

                this.metadata = response;
                return response.results || [];
            },

            /**
             * Override the default Backbone fetch to support atomic multi-request
             * loads.
             *
             * If a SolrQuery object is provided under the option baseSolrQuery,
             * it loads all the rows at that query using multiple requests. If
             * a url is provided instead it defaults to normal Backbone fetch
             * behavior.
             *
             * It behaves correctly in the case where `fetch` is called while
             * the preceding load is still ongoing.
             *
             * @param {Object=} options
             */
            fetch: function (options)
            {
                options = options || {};

                var baseRequest = options.baseSolrQuery;

                if (!baseRequest)
                {
                    Backbone.Collection.prototype.fetch.call(this, options);
                    return;
                }

                var fetchCount = ++this._fetchCount;
                var successCb = options.success;
                var loaded = 0;
                var collection = this;

                // Set default Solr parameters if needed
                baseRequest = this.setSolrQueryDefaults(baseRequest);

                // Set some sync option defaults we'll need for each request
                options = _.defaults({success: continueLoading}, options, {parse: true});

                // Set options for the initial request
                var requestOptions = _.defaults({
                    url: this.baseUrl() + '?' + baseRequest.toString()
                }, options);

                Backbone.sync('read', this, requestOptions);

                function continueLoading(response)
                {
                    // If another fetch has been fired then don't update the collection
                    if (fetchCount !== collection._fetchCount)
                        return;

                    // This is a modified version of the normal fetch callback code
                    var method = loaded === 0 ? 'reset' : 'set';
                    collection[method](response, requestOptions);
                    if (successCb) successCb(collection, response, requestOptions);
                    collection.trigger('sync', collection, response, requestOptions);

                    // If there are more results then continue to load
                    loaded += response.results.length;
                    if (response.numFound > loaded)
                    {
                        var request = baseRequest.extend({
                            params: {start: loaded}
                        });

                        // Create the options for the new request
                        // Note that we can't reuse options between requests because
                        // Backbone alters the option object
                        requestOptions = _.defaults({
                            url: collection.baseUrl() + '?' + request.toString(),
                            remove: false,
                            merge: false
                        }, options);

                        Backbone.sync('read', collection, requestOptions);
                    }
                }
            },

            /**
             * Extend a SolrQuery with default values if they were unset
             *
             * Specifically:
             *
             *  - set the default number of rows to 20
             *  - set the sort order to that given by the collection's dynamic comparison
             *    parameters, if those exist
             *
             * @param solrQuery
             * @returns {SolrQuery} the query which was passed in if the defaults were
             *   set, or an extended query
             */
            setSolrQueryDefaults: function (solrQuery)
            {
                var extension = null;

                // Fetch 20 rows at a time by default
                if (!_.has(solrQuery.params, 'rows'))
                {
                    extension = {rows: 20};
                }

                // Sort using the model's comparison function by default
                if (this.comparisonParameters && !_.has(solrQuery.params, 'sort'))
                {
                    var sort = this.comparisonParameters.get('sortBy') + ' ' +
                        (this.comparisonParameters.get('reverseSort') ? 'desc' : 'asc');

                    (extension = extension || {}).sort = sort;
                }

                if (extension)
                    return solrQuery.extend({params: extension});

                return solrQuery;
            }
        });
    }
);
