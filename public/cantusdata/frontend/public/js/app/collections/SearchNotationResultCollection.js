define(['underscore', 'backbone', 'qs', 'config/GlobalVars'], function (_, Backbone, Qs, GlobalVars)
{
    "use strict";

    /**
     * Collection for results of notation searches
     *
     * @constructor
     */
    return Backbone.Collection.extend({
        initialize: function (options)
        {
            this.updateParameters(options);
        },

        /**
         * Update the parameters used to build the URL
         *
         * @param options
         */
        updateParameters: function (options)
        {
            this.parameters = options || {};
        },

        url: function ()
        {
            var queryParams = {
                q: _.result(this.parameters, 'query'),
                type: _.result(this.parameters, 'field')
            };

            var manuscript = _.result(this.parameters, 'manuscript');

            if (manuscript)
                queryParams.manuscript = manuscript;

            return GlobalVars.siteUrl + "notation-search/?" + Qs.stringify(queryParams);
        },

        /**
         * Given a response of the format {numFound: ..., results: ...},
         * just take the list of results.
         *
         * @param response
         * @returns {Array}
         */
        parse: function (response)
        {
            return response && response.results || [];
        }
    });
});
