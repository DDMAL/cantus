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
            /* eslint-disable eqeqeq */

            // Use weak equality because less-than uses weak semantics as well.
            // Ideally values should be of the same type, however.
            if (a == b)
                return 0;

            /* eslint-enable eqeqeq */

            return a < b ? -1 : 1;
        }

        return Backbone.Collection.extend({
            // Sometimes overridden
            // TODO(wabain): find out what would override this and why
            searchPage: "search/",

            model: SearchResult,

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
            }
        }, {
            /**
             * Get a comparator function to the collection by the parameters
             * specified by the comparison model.
             *
             * Specifically, it looks for the following attributes:
             *
             *  - `sortBy` (string): the field to sort by
             *  - `reverseSort` (boolean): whether to reverse the sort order
             *
             * @param comparisonModel
             */
            getComparatorFunction: function (comparisonModel)
            {
                var fieldName = comparisonModel.get('sortBy');
                var reversed = comparisonModel.get('reverseSort');

                return function (itemA, itemB)
                {
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
            }
        });
    }
);
