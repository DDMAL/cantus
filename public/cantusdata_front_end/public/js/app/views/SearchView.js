define( ['App', 'backbone', 'marionette', 'jquery',
        "models/SolrDisjunctiveQueryBuilder",
        "views/CantusAbstractView",
        "views/SearchResultView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             SolrDisjunctiveQueryBuilder,
             CantusAbstractView,
             SearchResultView,
             GlobalEventHandler) {

        "use strict";

        /**
         * Provide an alert message to the user.
         */
        return Marionette.LayoutView.extend
        ({
            template: "#search-template",

            /**
             *
             */
            query: null,
            field: "all",

            /**
             * Some additional text added to all queries.  For example, you might
             * want this view to only search through chants.  In that case,
             * you would set this.queryPostScript to "AND type:cantusdata_chant".
             */
            queryPostScript: null,
            timer: null,

            /**
             * Some particular paramaters.
             */
            sort: "folio asc",

            // Subviews
            searchResultView: null,
            showManuscriptName: true,

            // Search template dictionary
            currentSearchFormTemplate: "all",
            searchFormTemplates: {},

            events: {},

            regions: {
                searchResultsRegion: ".search-results"
            },

            ui: {
                searchInputDiv: ".input-section",
                searchInput: ".search-input",
                searchFieldSelector: ".search-field"
            },

            initialize: function(options)
            {
                // The search form templates
                this.searchFormTemplates.all = _.template( $('#search-all-template').html());
                this.searchFormTemplates.mode = _.template( $('#search-mode-template').html());
                this.searchFormTemplates.volpiano = this.searchFormTemplates.all;
                this.searchFormTemplates.feast = this.searchFormTemplates.all;
                this.searchFormTemplates.office = this.searchFormTemplates.all;

                // If not supplied, the query is blank
                if (options !== undefined)
                {
                    // Is there a query?
                    if (options.query !== undefined)
                    {
                        this.query = options.query;
                    }
                    else
                    {
                        this.query = "";
                    }
                    // Is there a query post script?
                    if (options.queryPostScript !== undefined)
                    {
                        this.setQueryPostScript(options.queryPostScript);
                    }
                    else
                    {
                        // There is no postScript, but there still might be
                        // other parameters, such as sorting...
                        this.setQueryPostScript("");
                    }
                }
                this.searchResultView = new SearchResultView(
                    {
                        query: this.query,
                        showManuscriptName: this.showManuscriptName
                    }
                );
            },

            /**
             * Get the search field type selector value.
             */
            getSearchFieldTypeValue: function()
            {
                return encodeURIComponent(this.ui.searchFieldSelector.val());
            },

            /**
             * Get the search query value.
             *
             * @returns {*}
             */
            getSearchQueryValue: function()
            {
                return encodeURIComponent(this.ui.searchInput.val());
            },

            /**
             * Set this.queryPostScript.
             *
             * @param postScript string
             */
            setQueryPostScript: function(postScript)
            {
                this.queryPostScript = String(postScript) + "&sort=" + this.sort;
            },

            changeSearchField: function()
            {
                // Grab the field name
                var newField = this.getSearchFieldTypeValue();
                // We want to make sure that we aren't just loading the same template again
                if (this.searchFormTemplates[newField] !== this.searchFormTemplates[this.field])
                {
                    // Store the field
                    this.field = newField;
                    // Render with the new template
                    this.ui.searchInputDiv.html(
                        this.searchFormTemplates[String(this.field)](
                            {query: this.query}));
                    this.bindUIElements();
                }
                // We want to fire off a search
                this.newSearch();
            },

            /**
             * Take the value of the search input box and perform a search query
             * with it.  This function hits the API every time it is called.
             */
            newSearch: function()
            {
                // Grab the new search query
                var newQuery = this.getSearchQueryValue();
                // Grab the field name
                var fieldSelection = this.getSearchFieldTypeValue();
                if (newQuery !== this.query || fieldSelection !== this.field) {
                    this.query = newQuery;
                    this.field = fieldSelection;
                    if (newQuery === "")
                    {
                        // Empty search, so hide the searchResultView
                        this.searchResultView.hide();
                    }
                    else {
                        // Append the field selector if necessary!
                        if (fieldSelection !== "all")
                        {
                            // Split the query into multiple things
                            var queryList = decodeURIComponent(newQuery).split(",");
                            var disjunctive = new SolrDisjunctiveQueryBuilder(fieldSelection, queryList);
                            newQuery = disjunctive.getQuery();
                        }
                        if (this.queryPostScript !== null)
                        {
                            // Attach this.queryPostScript if available
                            this.searchResultView.changeQuery(newQuery + " " + this.queryPostScript, this.field);
                        }
                        else
                        {
                            // Set the new search results view
                            this.searchResultView.changeQuery(newQuery, this.field);
                        }
                    }
                }
            },

            /**
             * Register the events that are necessary to have search input.
             */
            registerEvents: function()
            {
                // Clear out the events
                this.events = {};
                // Register them
                this.events["change .search-input"] = "newSearch";
                this.events["change .search-field"] = "changeSearchField";
                this.events["input .search-input"] = "autoNewSearch";
                // Delegate the new events
                this.delegateEvents();
            },

            /**
             * Set the timer to perform a new search.
             * This is called when you want to avoid making multiple querie
             * very quickly.
             */
            autoNewSearch: function()
            {
                if (this.timer !== null)
                {
                    window.clearTimeout(this.timer);
                }
                // Flip this to self so that we don't lost our closure
                var self = this;
                this.timer = window.setTimeout(
                    function() {
                        self.newSearch();
                    }, 250);
            },

            onRender: function()
            {
                this.registerEvents();
                this.ui.searchInputDiv.html(
                            this.searchFormTemplates[this.field]({query: this.query}));
                // Render subviews
                this.searchResultsRegion.show(this.searchResultView);
                // Rebind the UI elements
                this.bindUIElements();
                GlobalEventHandler.trigger("renderView");
            }
        });
    });