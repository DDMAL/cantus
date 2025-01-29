import Marionette from 'marionette';

import _ from 'underscore';

export default Marionette.View.extend({
    tagName: "a",
    className: "list-group-item",
    attributes: {
        'href': '#'
    },

    template: _.template('<%= term %>'),


});
