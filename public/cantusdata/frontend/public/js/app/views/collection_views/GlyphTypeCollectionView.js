define(['marionette', "views/item_views/GlyphTypeView"],
    function(Marionette, GlyphTypeView)
    {

        "use strict";

        /**
         * A collection of glyph types.
         */
        return Marionette.CollectionView.extend({
            childView: GlyphTypeView,
            tagName: "ul"
        });
    });
