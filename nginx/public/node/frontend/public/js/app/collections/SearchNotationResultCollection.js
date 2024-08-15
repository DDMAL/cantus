import _ from 'underscore';
import Backbone from 'backbone';
import Qs from 'qs';
import GlobalVars from 'config/GlobalVars';

/**
 * Collection for results of notation searches
 *
 * @constructor
 */
export default Backbone.Collection.extend({
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
        this.numFound = response && response.numFound || 0;
        return response && response.results || [];
    }
});
