import Marionette from "marionette";

import template from './result-item.template.html';

export default Marionette.View.extend({
    template,
    tagName: 'tr',

    events: {
        'click .result-target': function (event) {
            event.preventDefault();
            this.trigger('showResult', this.model);
        }
    }
});
