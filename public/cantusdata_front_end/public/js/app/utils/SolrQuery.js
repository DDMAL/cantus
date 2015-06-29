define(["underscore", "marionette"], function (_, Marionette)
{
    // Match delimiters, "!", and (this is a bit hacky) strings which are entirely whitespace
    // FIXME(wabain): find a full spec of what should be escaped
    var SPECIAL_SOLR_QUERY_VALUE = /[()[\]{}!]|^\s+$/g;

    /**
     * @constructor
     *
     * Helper to construct queries to pass to the Solr server.
     *
     * - A field value is either a string, an array, or an object
     *   with the attributes `terms` (a list of Solr field values)
     *   and `connective`, where the value of connective is `AND`
     *   or `OR`.
     *
     * - A parameter is a key/value string to pass to Solr (e.g.
     *   sort: 'folio asc').
     *
     * @param options Initial fields and parameters
     */
    var SolrQuery = Marionette.Object.extend({
        initialize: function ()
        {
            _.bindAll(this, 'getSolrTerm');

            this.params = this.getOption('params') || {};
            this.fields = {};

            var fields = this.getOption('fields');

            if (fields)
            {
                _.forEach(fields, function (value, field)
                {
                    this.setField(field, value);
                }, this);
            }
        },

        /**
         * Set the given field to a value
         *
         * @param {string} field
         * @param {(string|array|Object)} value The value to set it to.
         * @param {string=} connective The connective to join the terms
         *   with if they are an array. (Default: `"AND"`)
         */
        setField: function (field, value, connective)
        {
            if (_.isArray(value))
            {
                value = {terms: value, connective: connective || 'AND'};
            }

            this.fields[field] = value;
        },

        /**
         * Return a copy of the query which is extended by the addition of the given fields
         * and parameters.
         *
         * @param options
         * @returns {SolrQuery}
         */
        extend: function (options)
        {
            var newFields = _.clone(this.fields);
            var newParams = _.clone(this.params);

            if (_.has(options, 'fields'))
                _.extend(newFields, options.fields);

            if (_.has(options, 'params'))
                _.extend(newParams, options.params);

            return new SolrQuery({
                fields: newFields,
                params: newParams
            });
        },

        /**
         *
         * @param value
         * @returns {*}
         */
        getSolrTerm: function (value)
        {
            if (_.isObject(value))
            {
                if (value.terms)
                {
                    if (value.terms.length > 1)
                    {
                        return '(' + _.map(value.terms, this.getSolrTerm).join(' ' + value.connective + ' ') + ')';
                    }
                    else if (value.terms.length === 1)
                    {
                        value = value.terms[0];
                    }
                    else
                    {
                        return '';
                    }
                }
            }

            return '(' + this.escapeSolrTerm(value) + ')';
        },

        /**
         * Return a string where characters that have special values in the
         * query syntax have been escaped
         *
         * FIXME: this escaping probably isn't comprehensive
         *
         * @param {string} value
         * @returns {string}
         */
        escapeSolrTerm: function (value)
        {
            return value.replace(SPECIAL_SOLR_QUERY_VALUE, '\\$&');
        },

        toString: function ()
        {
            var constructedTerms = [];

            var fields;

            if (_.has(this.fields, 'all'))
            {
                constructedTerms.push(this.getSolrTerm(this.fields.all));
                fields = _.omit(this.fields, 'all');
            }
            else
            {
                fields = this.fields;
            }

            _.forEach(fields, function(value, key)
            {
                constructedTerms.push(key + ':' + this.getSolrTerm(value));
            }, this);

            var urlQuery = {q: constructedTerms.join(' AND ')};
            _.extend(urlQuery, this.params);

            return _.map(urlQuery, function (value, key)
            {
                return key + '=' + encodeURIComponent(value);
            }).join('&');
        }
    });

    return SolrQuery;
});