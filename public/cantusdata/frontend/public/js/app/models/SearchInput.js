import Backbone from "backbone";

export default Backbone.Model.extend({
    defaults: {
        field: 'all',
        query: '',
        sortBy: 'folio',
        reverseSort: false
    }
});
