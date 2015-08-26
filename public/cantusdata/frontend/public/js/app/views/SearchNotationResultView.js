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
            'reset request sync': 'updateTable'
        },

        behaviors: {
            resize: {
                target: '.result-table-wrapper',
                allowSmaller: true
            }
        },

        ui: {
            tableWrapper: '.result-table-wrapper',
            table: 'table'
        },

        childEvents: function ()
        {
            return {
                showResult: this.triggerZoomToResult
            };
        },

        updateTable: function ()
        {
            if (this.collection.length)
            {
                this.ui.tableWrapper.show();
                this.triggerMethod('recalculate:size');
            }
            else
            {
                this.ui.tableWrapper.hide();
            }
        },

        triggerZoomToResult: function (view)
        {
            this.trigger('zoomToResult', view.model);
        },

        onRender: function ()
        {
            this.updateTable();
        }
    });
});