define(['underscore', 'config/GlobalVars'], function (_, GlobalVars)
{
    "use strict";

    /**
     * Generate a IIIF URL for a snippet of a page
     *
     * @param {String} siglumSlug The siglum slug of the manuscript to search
     * @param {Object} location The location of the manuscript to search, with attributes
     *
     *   - p: folio number
     *   - x, y: coordinates of the upper left point
     *   - w, h: width and height of the snippet
     *
     * @param {Object} dimensions The dimensions of the image to output, with attributes
     *   width and height (both optional).
     */
    return function pageSnippetUrl(siglumSlug, loc, dimens)
    {
        // FIXME: hard coding this path is awkward
        var filename = GlobalVars.divaImageDirectory + siglumSlug + '/' + siglumSlug + '_' + loc.p + '.jp2';
        var bounds = [loc.x, loc.y, loc.w, loc.h].join(',');

        var outputWidth = _.has(dimens, 'width') ? dimens.width : '';
        var outputHeight = _.has(dimens, 'height') ? dimens.height : '';
        var dimensions = outputWidth + ',' + outputHeight;

        var iiifQuery = filename + '/' + bounds + '/' + dimensions + '/0/native.jpg';

        return GlobalVars.iipImageServerUrl + '?IIIF=' + iiifQuery;
    };
});