define(['underscore', 'marionette'],
    function(_, Marionette)
    {

        "use strict";

        /**
         * View representing a single search result
         */
        return Marionette.ItemView.extend({
            template: "#search-result-item-template",

            // Note that having more than one tbody element is perfectly legal:
            // see permitted content in
            // <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>
            tagName: 'tbody',

            searchType: null,

            initialize: function ()
            {
                // FIXME(wabain): use mergeOptions after upgrading marionette
                this.searchType = this.getOption('searchType');
                this.query = this.getOption('query');
            },

            serializeData: function()
            {
                return {
                    infoFields: _.toArray(this.getOption('infoFields')),
                    searchType: this.searchType,
                    result: this.model.getFormattedData(this.searchType, this.query)
                };
            }
        });
    });
