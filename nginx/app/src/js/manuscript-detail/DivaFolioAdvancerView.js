import Marionette from 'marionette';
import $ from 'jquery';
import Radio from 'backbone.radio';

import template from './diva-folio-advancer.template.html';

var manuscriptChannel = Radio.channel('manuscript');
/**
 * A widget with buttons that controls
 */
export default Marionette.View.extend({
    template,

    ui:
    {
        nextButton: ".next-folio",
        previousButton: ".previous-folio",
        firstChantFolioButton: ".first-chant-folio"
    },

    events:
    {
        "click @ui.nextButton": "nextButtonCallbackHandler",
        "click @ui.previousButton": "previousButtonCallbackHandler",
        "click @ui.firstChantFolioButton": "firstChantFolioCallbackHandler",
    },

    /**
     * Get the Diva adapter.
     *
     * @returns {DivaAdapter}
     */
    getDivaAdapter: function () {
        return manuscriptChannel.request('diva');
    },

    /**
     * Advance to the next folio (one page, or a whole opening in book view).
     */
    nextButtonCallbackHandler: function (event) {
        // Don't follow the a href to "#"
        event.preventDefault();

        this.getDivaAdapter().goToNextPage();
    },

    /**
     * Go back to the previous folio (one page, or a whole opening in book view).
     */
    previousButtonCallbackHandler: function (event) {
        // Don't follow the a href to "#"
        event.preventDefault();

        this.getDivaAdapter().goToPreviousPage();
    },

    firstChantFolioCallbackHandler: function (event) {
        // Query which folio in the manuscript has the first chant
        var manuscript = manuscriptChannel.request('manuscript');
        var queryUrl = '/folio-set/manuscript/' + manuscript + '/';
        var divaAdapter = this.getDivaAdapter();
        $.get(queryUrl,
            function (data) {
                var firstFolioURI = data[0].image_uri;
                divaAdapter.gotoPageByURI(firstFolioURI);
            })
    }
});
