define( ['App', 'marionette', 'jquery'],
function(App, Marionette, $)
{

"use strict";

/**
 * A widget with buttons that controls
 */
return Marionette.ItemView.extend
({
    template: "#diva-folio-advancer-template",
    tagName: "nav",

    ui:
    {
        nextButton: "[name='next']",
        previousButton: "[name='previous']"
    },

    events:
    {
        "click @ui.nextButton": "nextButtonCallbackHandler",
        "click @ui.previousButton": "previousButtonCallbackHandler"
    },

    /**
     * Get the stored Diva data.
     *
     * @returns {*|jQuery}
     */
    getDivaData: function()
    {
        return $("#diva-wrapper").data('diva');
    },

    nextButtonCallbackHandler: function()
    {
        // We use divaData to call the diva functions
        var divaData = this.getDivaData();
        // Grab the current page
        var currentPageIndex = divaData.getCurrentPageIndex();
        // Tell Diva to go to the next page
        divaData.gotoPageByIndex(currentPageIndex + 1);
    },

    previousButtonCallbackHandler: function()
    {
        // We use divaData to call the diva functions
        var divaData = this.getDivaData();
        // Grab the current page
        var currentPageIndex = divaData.getCurrentPageIndex();
        // Tell Diva to go to the previous page
        divaData.gotoPageByIndex(currentPageIndex - 1);
    }
});
});