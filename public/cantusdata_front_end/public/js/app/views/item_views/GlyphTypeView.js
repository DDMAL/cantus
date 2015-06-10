define( ['App', 'marionette'],
    function(App, Marionette) {

        "use strict";

        /**
         * View representing a Glyph Type with count.
         */
        return Marionette.ItemView.extend({
            template: "#single-glyph-type-template",
            tagName: "li"
        });
    });
