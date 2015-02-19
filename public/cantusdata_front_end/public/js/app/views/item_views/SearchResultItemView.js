define( ['App', 'backbone', 'marionette'],
    function(App, Backbone, Marionette, template) {

        "use strict";

        /**
         * View representing a Search Result with count.
         */
        return Marionette.ItemView.extend({
            template: "#search-result-item-template",
            tagName: 'table class="table table-striped"',

            modelEvents: {
                "change": "render"
            },

            serializeData: function()
            {
                return {
                    results: this.model.getFormattedData()
                };
            }
        });
    });
