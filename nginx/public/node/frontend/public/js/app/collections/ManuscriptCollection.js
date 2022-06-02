import Backbone from "backbone";
import Manuscript from "models/Manuscript";

export default Backbone.Collection.extend({
    model: Manuscript
});
