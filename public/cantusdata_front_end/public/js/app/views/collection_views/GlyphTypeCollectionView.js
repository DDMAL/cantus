define( ['App', 'backbone', 'marionette', "views/item_views/GlyphTypeView"],
    function(App, Backbone, Marionette, GlyphTypeView) {

        "use strict";

        /**
         * A collection of glyph types.
         */
        return Marionette.CollectionView.extend({
            childView: GlyphTypeView,
            tagName: "ul"
        });
    });
