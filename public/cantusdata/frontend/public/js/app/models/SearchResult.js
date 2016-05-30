import _ from "underscore";
import Backbone from "backbone";
import { formatVolpianoResult, parseVolpianoSyllables } from 'utils/VolpianoDisplayHelper';

/* TODO(wabain): This model class is supposed to be generic over search result types - it can handle
 * manuscripts, chants, or whatever. In practice the only thing it's useful to search is chants.
 * Usages of this should be replaced with the normal Chant model. */

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
                    newElement.volpiano = formatVolpianoResult(newElement.full_text, result.volpiano, query, false);
                }
                else if (searchType === 'volpiano_literal')
                {
                    newElement.volpiano = formatVolpianoResult(newElement.full_text, result.volpiano, query, true);
                }
                else
                {
                    newElement.volpiano = parseVolpianoSyllables(newElement.full_text, result.volpiano);
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
