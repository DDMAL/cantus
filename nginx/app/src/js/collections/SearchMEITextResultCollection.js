import _ from 'underscore';
import Backbone from 'backbone';
import Qs from 'qs';
import GlobalVars from 'config/GlobalVars';

/**
 * Collection for results of searches of the text lines in a manuscript's MEI
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
            manuscript_id: _.result(this.parameters, 'manuscript'),
            hyphens: _.result(this.parameters, 'ignoreHyphens') ? 'ignore' : 'keep',
            multiline: _.result(this.parameters, 'multiline') ? 'true' : 'false'
        };

        return GlobalVars.siteUrl + "text-search/?" + Qs.stringify(queryParams);
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
