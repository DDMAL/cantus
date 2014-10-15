//var CantusAbstractView = require(["views/CantusAbstractView"]);
//var SearchResultView = require(["views/SearchResultView"]);

define( ['App', 'backbone', 'marionette', 'jquery',
        "models/SolrDisjunctiveQueryBuilder",
        "views/CantusAbstractView",
        "views/SearchResultView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $, SolrDisjunctiveQueryBuilder, CantusAbstractView, SearchResultView, GlobalEventHandler, template) {

        /**
         * Provide an alert message to the user.
         */
        return CantusAbstractView.extend
        ({
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

            // Subviews
            searchResultView: null,
            showManuscriptName: true,

            // Search template dictionary
            currentSearchFormTemplate: "all",
            searchFormTemplates: {},

            events: {},

            initialize: function(options)
            {
                _.bindAll(this, 'render', 'newSearch', 'autoNewSearch',
                    'changeSearchField', 'registerEvents');
                this.template= _.template($('#search-template').html());
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
                }
                this.searchResultView = new SearchResultView(
                    {
                        query: this.query,
                        showManuscriptName: this.showManuscriptName
                    }
                );
            },

            /**
             * Set this.queryPostScript.
             *
             * @param postScript string
             */
            setQueryPostScript: function(postScript)
            {
                this.queryPostScript = String(postScript);
            },

            changeSearchField: function()
            {
                // Grab the field name
                var newField = encodeURIComponent($(this.$el.selector + ' .search-field').val());
                // We want to make sure that we aren't just loading the same template again
                if (this.searchFormTemplates[newField] !== this.searchFormTemplates[this.field])
                {
                    // Store the field
                    this.field = newField;
                    // Render with the new template
                    $(this.$el.selector  + " .input-section").html(
                        this.searchFormTemplates[String(this.field)](
                            {query: this.query}));
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
                var newQuery = encodeURIComponent($(this.$el.selector + ' .search-input').val());
                // Grab the field name
                var fieldSelection = encodeURIComponent($(this.$el.selector + ' .search-field').val());
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
                this.timer = window.setTimeout(this.newSearch, 250);
            },

            render: function()
            {
                this.registerEvents();
                $(this.el).html(this.template());
                if (this.field in this.searchFormTemplates)
                {
                    $(this.$el.selector  + " .input-section").html(
                        this.searchFormTemplates[this.field]({query: this.query}));
                }
                else
                {
                    $(this.$el.selector  + " .input-section").html("Error!");
                }
                // Render subviews
                $(this.$el.selector + ' .search-results').html("SEARCH RESULT VIEW!");
                this.assign(this.searchResultView, this.$el.selector + ' .search-results');
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });