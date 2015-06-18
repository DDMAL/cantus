define(["jquery", "backbone", "config/GlobalVars"],
    function($, Backbone, GlobalVars) {

        "use strict";

        /**
         * This represents a search result.  It is experimental.
         */
        return Backbone.Model.extend({
            /**
             * Formats the data to be printed in a search result list.
             */
            getFormattedData: function(searchType, query)
            {
                // FIXME(wabain): some of this should be happening in model.parse, and some
                // in a template helper or something

                var result = this.attributes;

                var newElement = {};
                // Remove "cantusdata_" from the type string
                newElement.model = result.type.split("_")[1];
                newElement.name = result.Name;

                // Figure out what the name is based on the model in question
                switch(newElement.model)
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
                        newElement.folio = result.folio;
                        newElement.mode = result.mode;
                        newElement.office = result.office;
                        newElement.genre = result.genre;

                        if (searchType === 'volpiano')
                        {
                            newElement.volpiano = this.highlightVolpianoResult(result.volpiano, query);
                        }
                        else
                        {
                            newElement.volpiano = result.volpiano;
                        }

                        newElement.url = "/manuscript/" + result.manuscript_id + "/?folio=" + result.folio + "&chant=" + result.sequence;
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

                return newElement;
            },

            /**
             *  Take a volpiano result string and highlight the substrings
             *  that are part of the query.
             *
             * @param result volpiano result string
             * @returns {string} highlighted string
             */
            highlightVolpianoResult: function(result, query)
            {
                // Format the volpiano as a regex with optional dashes
                var regex = this.formatVolpianoWithDashesRegex(query);
                // Grab all matches from that regex
                var regexMatches = result.match(regex);

                // If something went wrong and there is no match, fail unobtrusively
                if (!regexMatches)
                {
                    console.error('Failed to find the match for', query, 'in Volpiano string', result);
                    return result;
                }

                // Highlight the matches with the proper span tag
                for (var i = 0; i < regexMatches.length; i++)
                {
                    // Add the span tag
                    result = result.replace(regexMatches[i], '<span class="bg-info">' + regexMatches[i] + '</span>');
                }

                return result;
            },

            /**
             * Create a RegEx matching volpiano with optional dashes from a string
             * representing a volpiano search query.
             *
             * So, "abc" becomes a-*b-*c-* etc.
             *
             * @param volpianoWithoutDashes string representing the volpiano without dashes
             * @returns {RegExp}
             */
            formatVolpianoWithDashesRegex: function(volpianoWithoutDashes)
            {
                // Empty string that we will fill up
                var outputAsString = "";

                // Normalize the case of the query: the Volpiano string will always
                // be lower-cased
                volpianoWithoutDashes = volpianoWithoutDashes.toLowerCase();

                for (var i = 0; i < volpianoWithoutDashes.length; i++)
                {
                    // Add the char at i
                    outputAsString += volpianoWithoutDashes.charAt(i);
                    // Add the optional dashes
                    outputAsString += "-*";
                }

                // Now we have a string representing a good regex, so we must
                // create an actual regex object
                return new RegExp(outputAsString, "g");
            }
        });
    }

);