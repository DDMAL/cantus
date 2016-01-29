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

            serializeData: function()
            {
                var searchType = this.getOption('searchType');
                var query = this.getOption('query');

                return {
                    infoFields: _.toArray(this.getOption('infoFields')),
                    searchType: searchType,
                    result: this.model.getFormattedData(searchType, query)
                };
            }
        });
    });
