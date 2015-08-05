define([
    "underscore",
    "backbone",
    "marionette",
    "utils/pageSnippetUrl"
], function (_, Backbone, Marionette, pageSnippetUrl)
{
    "use strict";

    var manuscriptChannel = Backbone.Radio.channel('manuscript');

    return Marionette.ItemView.extend({
        template: '#search-notation-result-item-view',
        tagName: 'tr',

        events: {
            'click .result-target': function (event)
            {
                event.preventDefault();
                this.trigger('showResult');
            }
        },

        initialize: function ()
        {
            var manuscript = manuscriptChannel.request('model:manuscript');

            this.siglumSlug = manuscript ? manuscript.get('siglum_slug') : null;
        },

        getThumbnails: function (boxes)
        {
            if (!this.siglumSlug)
            {
                return [];
            }

            return _.map(boxes, function (box)
            {
                return pageSnippetUrl(this.siglumSlug, box, {height: 30});
            }, this);
        },

        templateHelpers: function ()
        {
            return {
                contourGraph: function (semitones)
                {
                    var highest = 0, lowest = 0;
                    var height = 15, width = 50;

                    var relPitches = _.reduce(semitones, function (relPitches, semitone)
                    {
                        relPitches.push(_.last(relPitches) + semitone);
                        return relPitches;
                    }, [0]);

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
                            y: height - (range === 0 ? 0.5 : (pitch - lowest) / range) * height
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
                },
                thumbnails: _.bind(this.getThumbnails, this)
            };
        }
    });
});
