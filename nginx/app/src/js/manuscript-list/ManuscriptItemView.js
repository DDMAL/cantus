import _ from "underscore";
import Marionette from "marionette";

import template from './manuscript-item.template.html';

export default Marionette.View.extend({
    template,
    tagName: 'tr',
    ui: {
        tooltips: '[data-bs-toggle=tooltip]'
    },
    serializeData: function () {
        var data = _.pick(this.model.attributes, 'name', 'url', 'date', 'folio_count', 'chant_count', 'cantus_url');

        return _.extend(data, {
            short_name: this.model.get('provenance') + ', ' + this.model.get('siglum'),
        });

    },
    onRender: function () {
        // Initialize tooltips
        this.ui.tooltips.tooltip();
    }
});
