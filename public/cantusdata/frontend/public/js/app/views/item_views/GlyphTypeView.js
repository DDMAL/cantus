import Marionette from 'marionette';

/**
 * View representing a Glyph Type with count.
 */
export default Marionette.ItemView.extend({
    template: "#single-glyph-type-template",
    tagName: "li"
});
