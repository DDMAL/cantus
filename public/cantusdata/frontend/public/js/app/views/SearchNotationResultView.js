define(["underscore", "marionette"], function (_, Marionette)
{
    "use strict";

    return Marionette.CompositeView.extend({
        template: '#search-notation-result-list-view',

        childView: Marionette.ItemView.extend({
            template: '#search-notation-result-item-view',
            tagName: 'tr',

            events: {
                'click .result-target': function (event)
                {
                    event.preventDefault();
                    this.trigger('showResult');
                }
            },

            templateHelpers: {
                contourGraph: function (semitones)
                {
                    var highest = 0, lowest = 0;
                    var height = 15, width = 50;

                    var relPitches = _.reduce(semitones, function (relPitches, semitone)
                    {
                        if (relPitches.length === 0)
                            relPitches.push(0, semitone);
                        else
                            relPitches.push(relPitches[relPitches.length - 1] + semitone);

                        return relPitches;
                    }, []);

                    _.forEach(relPitches, function (pitch)
                    {
                        if (pitch > highest)
                            highest = pitch;
                        else if (pitch < lowest)
                            lowest = pitch;
                    });

                    var range = highest - lowest;
                    var stretch = relPitches.length === 1 ? 0.5 : relPitches.length - 1;

                    var points = _.map(relPitches, function (pitch, index)
                    {
                        return {
                            x: (index / stretch) * width,
                            y: (range === 0 ? 0.5 : (pitch - lowest) / range) * height
                        };
                    }, []);

                    var path = _.map(points, function (p, index)
                    {
                        return (index === 0 ? 'M' : 'L') + p.x + ' ' + p.y;
                    }).join('');

                    var circles = _.map(points, function (p)
                    {
                        return '<circle fill="black" r="2" cx="' + p.x + '" cy="' + p.y + '" />';
                    }).join('');

                    var padding = 2;
                    var viewBox = [-padding, -padding, width + padding * 2, height + padding * 2].join(' ');

                    return '<svg width="' + width + '" height="' + height + '" viewBox="' + viewBox + '">' +
                        '<path stroke="black" fill="none" d="' + path + '"/>' +
                        circles +
                        '</svg>';
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

            if (message)
                this.ui.resultHeading.html('<h4>' + message + '</h4>');
            else
                this.ui.resultHeading.empty();

            this.updateTable();
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