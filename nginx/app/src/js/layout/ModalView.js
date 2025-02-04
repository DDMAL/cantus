import Marionette from "marionette";
import $ from 'jquery';

import template from './modal.template.html';

/**
 * Draw a modal box containing a particular view.
 * This view follows the visitor design pattern.
 *
 * @type {*|void}
 */
export default Marionette.View.extend({
    template,

    regions: {
        body: '.modal-body'
    },

    events: {
        "hidden.bs.modal": "modalDismissCallback"
    },

    initialize: function (options) {
        this.title = options.title;
        this.visitorView = options.view;
        this.modalId = options.modalId;
    },

    onRender: function () {
        // Render out the modal template
        if (this.visitorView !== null) {
            this.getRegion('body').show(this.visitorView);
        }
    },

    serializeData: function () {
        return {
            title: this.title,
            modalId: this.modalId
        };
    },

    modalDismissCallback: function (event) {
        if (this.modalId == "aboutVolModal") {
            if ($('#manuscript-search-pane').length == 0) {
                $('#searchModal').modal('show');
            }
        }
    }
});
