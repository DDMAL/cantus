define(["underscore", "backbone", "models/SearchResult", "config/GlobalVars"],
    function(_, Backbone, SearchResult, GlobalVars)
    {

        "use strict";

        return Backbone.Collection.extend({
            // Sometimes overridden
            // TODO(wabain): find out what would override this and why
            searchPage: "search/",

            model: SearchResult,

            initialize: function()
            {
                this._fetchCount = 0;
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

                // Set some option defaults we'll always need
                options = _.defaults({success: continueLoading}, options, {parse: true});

                // Fetch 20 rows at a time by default
                if (!_.has(baseRequest.params, 'rows'))
                {
                    baseRequest = baseRequest.extend({
                        params: {rows: 20}
                    });
                }

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

            }
        });
    }
);
