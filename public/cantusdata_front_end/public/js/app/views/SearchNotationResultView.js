define(["marionette"], function (Marionette)
{
    "use strict";

    return Marionette.CompositeView.extend({
        template: '#search-notation-result-list-view',

        childView: Marionette.ItemView.extend({
            template: '#search-notation-result-item-view',
            tagName: 'tr',

            events: {
                'click .result-index': function (event)
                {
                    event.preventDefault();
                    this.trigger('showResult');
                }
            }
        }),

        childViewContainer: 'tbody',

        collectionEvents: {
            reset: 'showNoRequest',
            request: 'showPendingRequest',
            sync: 'showReceivedRequest'
        },

        ui: {
            table: 'table',
            resultHeading: '.result-heading'
        },

        childEvents: function ()
        {
            return {
                showResult: this.triggerZoomToResult
            };
        },

        showNoRequest: function (collection, options)
        {
            var message = _.result(options, 'message');

            if (collection.length)
                this.ui.table.show();
            else
                this.ui.table.hide();

            if (message)
                this.ui.resultHeading.html('<h4>' + message + '</h4>');
            else
                this.ui.resultHeading.empty();
        },

        showPendingRequest: function ()
        {
            this.ui.resultHeading.html(
                '<h3>' + this.collection.parameters.fieldName + ' search</h3>' +
                '<h4>Searching...</h4>' +
                '<img class="center-block" src="/static/img/loading.gif">'
            );

            this.ui.table.hide();
        },

        showReceivedRequest: function ()
        {
            this.ui.resultHeading.html(
                "<h3>" + this.collection.parameters.fieldName + " search</h3>" +
                "<h4>" + this.collection.length + ' results found for query "' +
                decodeURIComponent(this.collection.parameters.query) + '"</h4>'
            );

            this.ui.table.show();
        },

        triggerZoomToResult: function (view)
        {
            this.trigger('zoomToResult', view.model);
        }
    });
});