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

    /**
     * Go to the first page, in viewer order, that has a folio record. Folio
     * numbers can differ from viewer order (Salzinnes's 001r is page 21).
     */
    firstChantFolioCallbackHandler: function (event) {
        // Prevent adding "#" to the end of the URL
        event.preventDefault();

        var divaAdapter = this.getDivaAdapter();
        // Empty until the viewer has loaded
        var pageURIs = divaAdapter ? divaAdapter.getAllPageURIs() : [];
        if (pageURIs.length === 0)
            return;

        var manuscript = manuscriptChannel.request('manuscript');
        $.get('/folio-set/manuscript/' + manuscript + '/', (folios) => {
            if (this.isDestroyed())
                return;

            var folioImageURIs = new Set(folios.map(folio => folio.image_uri));
            var firstFolioURI = pageURIs.find(uri => folioImageURIs.has(uri));
            if (firstFolioURI)
                divaAdapter.gotoPageByURI(firstFolioURI);
            else
                alert("The first chant's page could not be found in the viewer.");
        });
    }
});
