import _ from "underscore";
import Backbone from "backbone";

/* TODO(wabain): This model class is supposed to be generic over search result types - it can handle
 * manuscripts, chants, or whatever. In practice the only thing it's useful to search is chants.
 * Usages of this should be replaced with the normal Chant model. */

// Cache the Volpiano query which  was last turned into a regex
var lastVolpianoQuery = null,
    lastVolpianoRegex = null,
    lastLiteralVolpianoQuery = null,
    lastLiteralVolpianoRegex = null,
    volpianoMap = {};

// Build a mapping of equivalent Volpiano characters
_.forEach(['iwxyz', 'IWXYZ', 'eEmM', 'fFnN', 'gG9)oO', 'hHaApP', 'jJbBqQ', 'kKcCrR', 'lLdDsS'],
function (equivalent)
{
    _.forEach(equivalent, function (value)
    {
        volpianoMap[value] = equivalent;
    });
});

/**
 * This represents a search result.  It is experimental.
 */
export default Backbone.Model.extend({
    /**
     * Formats the data to be printed in a search result list.
     */
    getFormattedData: function(searchType, query)
    {
        // FIXME(wabain): some of this should be happening in model.parse, and some
        // in a template helper or something

        // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

        var result = this.attributes;

        var newElement = {};
        // Remove "cantusdata_" from the type string
        newElement.model = result.type.split("_")[1];
        newElement.name = result.Name;

        // Figure out what the name is based on the model in question
        switch (newElement.model)
        {
            case "manuscript":
                newElement.name = result.name;
                // Build the url
                newElement.url = "/" + newElement.model + "/" + result.item_id + "/";
                break;

            case "chant":
                newElement.name = result.incipit;
                // Build the url
                // We have stored the manuscript name in Solr
                newElement.manuscript = result.manuscript_name_hidden;

                _.extend(newElement, _.pick(result, [
                    "feast",
                    "office",
                    "genre",
                    "position",
                    "mode",
                    "differentia",
                    "finalis",
                    "folio",
                    "cantus_id",
                    "full_text"
                ]));

                newElement.mode = this._getFormattedMode(newElement.mode);

                if (searchType === 'volpiano')
                {
                    newElement.volpiano = this.highlightVolpianoResult(result.volpiano, query, false);
                }
                else if (searchType === 'volpiano_literal')
                {
                    newElement.volpiano = this.highlightVolpianoResult(result.volpiano, query, true);
                }
                else
                {
                    newElement.volpiano = result.volpiano;
                }

                newElement.url = "/manuscript/" + result.manuscript_id + "/?folio=" + result.folio +
                    "&chant=" + result.sequence;
                break;

            case "concordance":
                newElement.name = result.name;
                // Build the url
                newElement.url = "/" + newElement.model + "/" + result.item_id + "/";
                break;

            case "folio":
                newElement.name = result.name;
                // Build the url
                newElement.url = "/" + newElement.model + "/" + result.item_id + "/";
                break;
        }

        // jscs:enable

        return newElement;
    },

    /**
     *  Take a volpiano result string and highlight the substrings
     *  that are part of the query.
     *
     * @param result volpiano result string
     * @returns {string} highlighted string
     */
    highlightVolpianoResult: function(result, query, onlyLiteralMatches)
    {
        // Format the Volpiano as a lenient regex
        var regex = this.getVolpianoRegex(query, onlyLiteralMatches);

        if (!regex)
            return result;

        var highlighted = result.replace(regex, '<span class="bg-info">$&</span>');

        // If something went wrong and there is no match, fail unobtrusively
        /* eslint-disable no-console */
        if (highlighted === result && console && console.error)
        {
            console.error('Failed to find the match for', query, 'in Volpiano string', result, 'with regex', regex);
        }
        /* eslint-enable no-console */

        return highlighted;
    },

    /**
     * Create a RegExp which supports lenient matching against a Volpiano query.
     * Its behaviour should match that in the Solr installation at
     * mapping-ExtractVolpianoNotes.txt
     *
     * TODO: if we ever add highlighting for other fields, it would be good to
     * use Solr's built in highlighting functionality. But configuring that to
     * work character by character is non-trivial, so we'll just highlight on the
     * client side for now.
     *
     * @param volpiano {string} a Volpiano query
     * @returns {RegExp}
     */
    getVolpianoRegex: function(volpiano, onlyLiteralMatches)
    {
        // Use a cached regex if one is available
        if (!onlyLiteralMatches && volpiano === lastVolpianoQuery)
            return lastVolpianoRegex;
        if (onlyLiteralMatches && volpiano === lastLiteralVolpianoQuery)
            return lastLiteralVolpianoRegex;

        // Empty string that we will fill up
        var outputAsString = "";

        var queryLength = volpiano.length;

        for (var i = 0; i < queryLength; i++)
        {
            var symbol = volpiano.charAt(i);

            // Use this variable to check if the symbol is a dash and a
            // literal search is being performed.
            var isLiteralDash = onlyLiteralMatches && symbol === '-';

            if (!(symbol in volpianoMap) && !isLiteralDash)
                continue;

            // If this is not the start of the regex, allow optional
            // characters in between the new character and the prior ones
            // Add the dash symbol to the optional characters list if not
            // performing a literal search
            if (outputAsString)
                outputAsString += "[" + (onlyLiteralMatches ? '' : '-') + "1-7]*";

            outputAsString += isLiteralDash ? '-' : '[' + volpianoMap[symbol] + ']';
        }

        // Now we have a string representing a good regex, so we must
        // create an actual regex object
        var regex = null;
        if (outputAsString)
            regex = new RegExp(outputAsString, "g");

        // Cache the generated regex
        if (onlyLiteralMatches)
        {
            lastLiteralVolpianoQuery = volpiano;
            lastLiteralVolpianoRegex = regex;
        }
        else
        {
            lastVolpianoQuery = volpiano;
            lastVolpianoRegex = regex;
        }


        return regex;
    },

    /**
     * Formats the mode to remove all occurences of "No music" and
     * replace "Chant in Transposition" by "T"
     * @param mode {string} the mode as returned from the server
     * @returns {string}
     * @private
     */
    _getFormattedMode: function(mode)
    {
        mode = mode.replace("No music", "");
        mode = mode.replace("Chant in Transposition", "T");
        mode = mode.replace("Formulaic", "F");
        mode = mode.replace("Uncertain", "U");
        mode = mode.replace("Responsory (special)", "R");
        return mode;
    }
});
