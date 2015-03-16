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

            initialize: function(pQuery)
            {
                this.setQuery(pQuery);
            },

            setQuery: function(query)
            {
                this.url = GlobalVars.siteUrl + this.searchPage + query;
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

                _.each(this.get("results"), function(current)
                {
                    var newElement = {};
                    // Remove "cantusdata_" from the type string
                    newElement.model = current.type.split("_")[1];
                    newElement.name = current.Name;

                    // Figure out what the name is based on the model in question
                    switch(newElement.model)
                    {
                        case "manuscript":
                            newElement.name = current.name;
                            // Build the url
                            newElement.url = "/" + newElement.model + "/" + current.item_id + "/";
                            break;

                        case "chant":
                            newElement.name = current.incipit;
                            // Build the url
                            // We have stored the manuscript name in Solr
                            newElement.manuscript = current.manuscript_name_hidden;
                            newElement.folio = current.folio;
                            newElement.volpiano = current.volpiano;
                            newElement.url = "/manuscript/" + current.manuscript_id + "/?folio=" + current.folio + "&chant=" + current.sequence;
                            break;

                        case "concordance":
                            newElement.name = current.name;
                            // Build the url
                            newElement.url = "/" + newElement.model + "/" + current.item_id + "/";
                            break;

                        case "folio":
                            newElement.name = current.name;
                            // Build the url
                            newElement.url = "/" + newElement.model + "/" + current.item_id + "/";
                            break;
                    }
                    output.push(newElement);
                });
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
            }
        });
    }

);