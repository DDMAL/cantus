define(['marionette'],
    function(Marionette) {

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

            showManuscriptName: true,
            searchType: null,

            initialize: function (options)
            {
                // FIXME(wabain): use mergeOptions after upgrading marionette
                if ('showManuscriptName' in options) {
                    this.showManuscriptName = options.showManuscriptName;
                }

                if ('searchType' in options) {
                    this.searchType = options.searchType;
                }
            },

            serializeData: function()
            {
                // FIXME(wabain): this is terrible, but I'll be refactoring
                // out the code that relies on having the index anyway
                var index = this.model.collection.indexOf(this.model);

                return {
                    index: index,
                    showManuscriptName: this.showManuscriptName,
                    searchType: this.searchType,
                    result: this.model.getFormattedData()
                };
            }
        });
    });
