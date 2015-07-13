define(["underscore", "backbone"],
    function(_, Backbone)
    {

        "use strict";

        // Cache the Volpiano query which  was last turned into a regex
        var lastVolpianoQuery = null,
            lastVolpianoRegex = null,
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
        return Backbone.Model.extend({
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
            highlightVolpianoResult: function(result, query)
            {
                // Format the Volpiano as a lenient regex
                var regex = this.getVolpianoRegex(query);

                var highlighted = result.replace(regex, '<span class="bg-info">$&</span>');

                // If something went wrong and there is no match, fail unobtrusively
                if (highlighted === result)
                {
                    // jshint devel:true
                    console.error('Failed to find the match for', query, 'in Volpiano string', result);
                }

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
            getVolpianoRegex: function(volpiano)
            {
                // Use a cached regex if one is available
                if (volpiano === lastVolpianoQuery)
                    return lastVolpianoRegex;

                // Empty string that we will fill up
                var outputAsString = "";

                var queryLength = volpiano.length;

                for (var i = 0; i < queryLength; i++)
                {
                    var symbol = volpiano.charAt(i);

                    // Ignore unsupported characters
                    if (!(symbol in volpianoMap))
                        continue;

                    // If this is not the start of the regex, allow optional
                    // characters in between the new character and the prior ones
                    if (outputAsString)
                        outputAsString += "[-1-7]*";

                    outputAsString += '[' + volpianoMap[symbol] + ']';
                }

                // Now we have a string representing a good regex, so we must
                // create an actual regex object
                var regex = new RegExp(outputAsString, "g");

                // Cache the generated regex
                lastVolpianoQuery = volpiano;
                lastVolpianoRegex = regex;

                return regex;
            }
        });
    }

);