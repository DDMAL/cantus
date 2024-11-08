import _ from 'underscore';

/**
 * Generate a IIIF URL for a snippet of a page
 *
 * @param {Object} location The location of the manuscript to search, with attributes
 *
 *   - p: folio number
 *   - x, y: coordinates of the upper left point
 *   - w, h: width and height of the snippet
 *
 * @param {Object} dimensions The dimensions of the image to output, with attributes
 *   width and height (both optional).
 */
export default function pageSnippetUrl(loc, dimens)
{
    var filename = loc.p;
    var bounds = [loc.x, loc.y, loc.w, loc.h].join(',');

    var outputWidth = _.has(dimens, 'width') ? dimens.width : '';
    var outputHeight = _.has(dimens, 'height') ? dimens.height : '';
    var dimensions = outputWidth + ',' + outputHeight;

    var iiifQuery = filename + '/' + bounds + '/' + dimensions + '/0/default.jpg';

    return iiifQuery;
}
