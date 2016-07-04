import Backbone from "backbone";

export default Backbone.Model.extend({
    initialize: function(url)
    {
        this.url = url;
    }
});
