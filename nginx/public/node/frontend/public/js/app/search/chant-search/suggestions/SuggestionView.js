import Marionette from 'marionette';

import template from './suggestion.template.html';

export default Marionette.View.extend({
    tagName: "a",
    className: "list-group-item",
    attributes: {
        'href': '#'
    },

    template: template
});
