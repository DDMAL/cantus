define(["jquery", "backbone", "config/GlobalVars"],
    function($, Backbone, GlobalVars) {

        "use strict";

        /**
         * This represents a search result.  It is experimental.
         */
        return Backbone.Model.extend
        ({
            // Sometimes overridden
            searchPage: "search/?q=",

            searchType: undefined,

            initialize: function(pQuery)
            {
                this.setQuery(pQuery);
            },

            /**
             * Set the query.
             *
             * @param query
             */
            setQuery: function(query)
            {
                this.url = GlobalVars.siteUrl + this.searchPage + query;
            },

            /**
             * Set the type of query.
             *
             * @param type
             */
            setType: function(type)
            {
                this.searchType = String(type);
            },

            /**
             * Get the type of search.
             *
             * @returns {*}
             */
            getSearchType: function()
            {
                return this.searchType;
            },

            /**
             * Get the query field with the manuscript selection stripped.
             *
             * @returns {*}
             */
            getQueryWithoutManuscript: function()
            {
                var fullQuery = this.get("query");

                if (fullQuery !== undefined)
                {
                    return this.get("query").replace(/AND manuscript:"[^\"]*"/g, '');
                }
                else
                {
                    return "";
                }
            },

            /**
             * Formats the data to be printed in a search result list.
             */
            getFormattedData: function()
            {
                var output = [];

                //_.each(this.get("results"), function(current)

                var results = this.get("results");

                console.log("Results:", results);

                if (results !== undefined)
                {
                    for (var i = 0; i < results.length; i++)
                    {
                        var newElement = {};
                        // Remove "cantusdata_" from the type string
                        newElement.model = results[i].type.split("_")[1];
                        newElement.name = results[i].Name;

                        // Figure out what the name is based on the model in question
                        switch(newElement.model)
                        {
                            case "manuscript":
                                newElement.name = results[i].name;
                                // Build the url
                                newElement.url = "/" + newElement.model + "/" + results[i].item_id + "/";
                                break;

                            case "chant":
                                newElement.name = results[i].incipit;
                                // Build the url
                                // We have stored the manuscript name in Solr
                                newElement.manuscript = results[i].manuscript_name_hidden;
                                newElement.folio = results[i].folio;
                                newElement.volpiano = this.highlightVolpianoResult(results[i].volpiano);
                                newElement.url = "/manuscript/" + results[i].manuscript_id + "/?folio=" + results[i].folio + "&chant=" + results[i].sequence;
                                break;

                            case "concordance":
                                newElement.name = results[i].name;
                                // Build the url
                                newElement.url = "/" + newElement.model + "/" + results[i].item_id + "/";
                                break;

                            case "folio":
                                newElement.name = results[i].name;
                                // Build the url
                                newElement.url = "/" + newElement.model + "/" + results[i].item_id + "/";
                                break;
                        }
                        output.push(newElement);
                    }
                }

                return output;
            },

            /**
             * An empty search is empty.
             */
            defaults: function()
            {
                return {
                    results: []
                };
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
                // Try to match the regex first
                var regexMatch = this.get("query").match(/volpiano: ?\(\"([^\"]*)\"\)/);

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