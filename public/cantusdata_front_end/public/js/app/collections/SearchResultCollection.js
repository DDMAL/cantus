define(["jquery", "backbone", "models/SearchResult", "config/GlobalVars"],
    function($, Backbone, SearchResult, GlobalVars)
    {

        "use strict";

        return Backbone.Collection.extend({
            // Sometimes overridden
            // TODO(wabain): find out what would override this and why
            searchPage: "search/",

            model: SearchResult,

            initialize: function(pQuery)
            {
                this.setQuery(pQuery || '');
            },

            /**
             * Set the query.
             *
             * @param query
             */
            setQuery: function(query)
            {
                this.query = '' + query;
            },

            /**
             * Return the composed URL
             *
             * @returns {string}
             */
            url: function ()
            {
                return GlobalVars.siteUrl + this.searchPage + '?' + this.query;
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
            }
        });
    }
);
