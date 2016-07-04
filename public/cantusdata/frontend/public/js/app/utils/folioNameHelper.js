/**
 * Escape a string so that it can be used searched for literally in a regex.
 * Implementation adapted from Backbone.Router._routeToRegExp
 */
function _escapeRegex(s)
{
    return s.replace(/[\-{}\[\]+?.,\\\^$|#\s]/g, '\\$&');
}

/**
 * Return a regex which matches a lenient form of the given folio name. Handle
 * leading zeros for numerical folio names, prefix characters (for appendices,
 * etc.) and suffix characters (e.g. r and v for recto and verso).
 *
 * Given a bare page number, it will automatically match it with a recto page
 * with that number.
 *
 * Examples: Suppose the folios are named 0000a, 0000b, 001r, 001v, and A001r
 *
 *   - 0a would match 0000a
 *   - a1 would match A001r
 *   - 0001 would match 001r
 *
 * @param folio {string}
 * @returns {RegExp} A RegExp for lenient matching
 */
export default {
    getMatcher(folio)
    {
        if (!folio)
            return null;

        // Try to split the folio into the following components:
        //   - an optional non-numerical leading value
        //   - an integer value (with leading zeros stripped)
        //   - an optional non-numerical trailing value
        var coreNumber = /^\s*([^0-9]*)0*([1-9][0-9]*|0)([^0-9]*)\s*$/.exec(folio);

        if (!coreNumber)
        {
            // If the core number detection failed, just strip whitespace and get a case-insensitive regex
            return new RegExp('^' + _escapeRegex(folio.replace(/(^\s+|\s+$)/g, '')) + '$', 'i');
        }

        var leading = coreNumber[1],
            number = coreNumber[2],
            trailing = coreNumber[3];

        leading = _escapeRegex(leading);

        if (trailing)
        {
            trailing = _escapeRegex(trailing);
        }
        else
        {
            // If there is no trailing value, then allow for a recto suffix by default
            trailing = 'r?';
        }

        // Get a case-insensitive regex which allows any number of leading zeros
        // and then the number
        return new RegExp('^' + leading + '0*' + number + trailing + '$', 'i');
    }
};
