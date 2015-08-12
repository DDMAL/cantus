define(["marionette"], function (Marionette)
{
    "use strict";

    return Marionette.ItemView.extend({
        template: '#manuscript-item-template',
        tagName: 'li',

        templateHelpers: {
            // Map to the Cantus URLs for the various manuscripts
            // Let this be a warning about the danger of non-meaningful URLs, I guess
            cantusUrls: {
                'cdn-hsmu-m2149l4': 'http://cantus.uwaterloo.ca/source/123723',
                'ch-sgs-390': 'http://cantus.uwaterloo.ca/source/123717',
                'ch-sgs-391': 'http://cantus.uwaterloo.ca/source/123718',
                'nl-uu-406': 'http://cantus.uwaterloo.ca/source/123641'
            }
        }
    });
});