define(['underscore', 'backbone', 'config/GlobalVars'], function (_, Backbone, GlobalVars)
{
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
            var url = GlobalVars.siteUrl +
                "notation-search/?q=" + _.result(this.parameters, 'query') +
                "&type=" + _.result(this.parameters, 'field');

            var manuscript = _.result(this.parameters, 'manuscript');
            if (manuscript)
                url += "&manuscript=" + manuscript;

            return url;
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
