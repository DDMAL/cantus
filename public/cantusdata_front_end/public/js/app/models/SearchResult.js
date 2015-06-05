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
            getFormattedData: function()
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
                        newElement.volpiano = this.highlightVolpianoResult(result.volpiano);
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
            highlightVolpianoResult: function(result)
            {
                if (!(this.metadata && this.metadata.query))
                    return null;

                // Try to match the regex first
                var regexMatch = this.metadata.query.match(/volpiano: ?\(\"([^\"]*)\"\)/);

                // Handle the case where there is no volpiano query
                if (regexMatch === null || regexMatch === undefined)
                    return result;

                // The query string will always be the second value in the array
                var rawVolpianoQuery = regexMatch[1];

                // Format the volpiano as a regex with optional dashes
                var regex = this.formatVolpianoWithDashesRegex(rawVolpianoQuery);
                // Grab all matches from that regex
                var regexMatches = result.match(regex);

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