define([
    "underscore",
    "marionette",
    "views/SearchNotationResultItemView"
],
function (_, Marionette, SearchNotationResultItemView)
{
    "use strict";

    return Marionette.CompositeView.extend({
        template: '#search-notation-result-list-template',

        childView: SearchNotationResultItemView,

        childViewContainer: 'tbody',

        collectionEvents: {
            reset: 'showNoRequest',
            request: 'showPendingRequest',
            sync: 'showReceivedRequest'
        },

        ui: {
            table: 'table'
        },

        childEvents: function ()
        {
            return {
                showResult: this.triggerZoomToResult
            };
        },

        showNoRequest: function ()
        {
            this.updateTable();
        },

        showPendingRequest: function ()
        {
            this.ui.table.hide();
        },

        showReceivedRequest: function ()
        {
            this.updateTable();
        },

        updateTable: function ()
        {
            if (this.collection.length)
                this.ui.table.show();
            else
                this.ui.table.hide();
        },

        triggerZoomToResult: function (view)
        {
            this.trigger('zoomToResult', view.model);
        },

        onRender: function ()
        {
            if (this.collection.length)
                this.showReceivedRequest();
            else
                this.showNoRequest(this.collection);
        }
    });
});