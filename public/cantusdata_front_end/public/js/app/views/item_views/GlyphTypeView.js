define( ['App', 'backbone', 'marionette'],
    function(App, Backbone, Marionette, template) {

        "use strict";

        /**
         * View representing a Glyph Type with count.
         */
        return Marionette.ItemView.extend({
            template: "#single-glyph-type-template",
            tagName: "li"
        });
    });
