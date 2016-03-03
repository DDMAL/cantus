import Marionette from 'marionette';
import GlyphTypeView from "views/item_views/GlyphTypeView";

/**
 * A collection of glyph types.
 */
export default Marionette.CollectionView.extend({
    childView: GlyphTypeView,
    tagName: "ul"
});
