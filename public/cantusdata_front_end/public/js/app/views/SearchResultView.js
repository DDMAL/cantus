define( ['App', 'backbone', 'marionette', 'jquery',
        "models/SearchResult",
        "views/CantusAbstractView",
        "views/PaginationView",
        "views/item_views/SearchResultItemView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             SearchResult,
             CantusAbstractView,
             PaginationView,
             SearchResultItemView,
             GlobalEventHandler,
             template) {

        return Marionette.LayoutView.extend
        ({
            template: "#search-result-template",

            showManuscriptName: null,
            pageSize: 10,
            currentPage: null,
            paginationView: null,
            query: null,
            field: null,

            regions: {
                resultRegion: ".result-region",
                paginationRegion: ".pagination-region"
            },

            initialize: function(options)
            {
                _.bindAll(this, 'render', 'updatePage', 'changeQuery',
                    'updatePaginationView', 'registerClickEvents',
                    'buttonClickCallback');

                this.currentPage = 1;
                this.model = new SearchResult();

                if (options.query !== undefined)
                {
                    this.model.setQuery(options.query);
                    this.query = options.query;
                }
                if (options.showManuscriptName !== undefined)
                {
                    // The client might not want to see the manuscript name
                    this.showManuscriptName = options.showManuscriptName;
                }

                // Create the paginationView
                this.paginationView = new PaginationView(
                    {
                        currentPage: 0,
                        elementCount: 0,
                        pageSize: this.pageSize
                    }
                );

                // Query the search result
                this.model.fetch({success: this.updatePaginationView});
                this.listenTo(this.model, 'sync', this.registerClickEvents);
                this.listenTo(this.paginationView, 'change', this.updatePage);
                //this.listenTo(this.model, 'sync', this.updatePaginationView);
            },

            /**
             * Register the events for clicking on a search result.
             */
            registerClickEvents: function()
            {
                // Clear out the events
                this.events = {};
                // Menu items
                for (var i = 0; i < this.model.get("results").length; i++)
                {
                    this.events["click .search-result-" + i] = "buttonClickCallback";
                }
                // Delegate the new events
                this.delegateEvents();
            },

            buttonClickCallback: function(event)
            {
                // Stop the page from auto-reloading
                event.preventDefault();
                // Figure out which button was clicked on
                var splitName = event.target.className.split("-");
                var newIndex = parseInt(splitName[splitName.length - 1], 10);
                // Redirect us to the new url!
                Backbone.history.navigate(this.model.getFormattedData()[newIndex].url,
                    {trigger: true});
            },

            /**
             * Set the model's query string and fetch results from the restful API.
             *
             * @param query string
             * @param field string
             */
            changeQuery: function(query, field)
            {
                this.currentPage = 1;
                this.model.setQuery(query);
                this.query = String(query);
                this.field = String(field);
                this.model.fetch({success: this.updatePaginationView});
            },

            /**
             * Rebuild the pagination view with the latest data from the model.
             */
            updatePaginationView: function()
            {
                // Update the paginator parameters.
                this.paginationView.setParams(
                    this.model.get("numFound"),
                    this.pageSize,
                    this.currentPage);

                // Render it
                this.paginationView.render();
            },

            /**
             * Grab the page number from the paginator
             */
            updatePage: function(args)
            {
                // Grab the page from the event arguments.  Make sure it's over 0.
                this.currentPage = Math.max(args.page, 0);
                // Rebuild the model with a modified query.  If the page is less than 0 then make it 0
                this.model.setQuery(this.query + "&start=" + (this.pageSize * (Math.max(this.currentPage - 1,0))));
                this.model.fetch();
            },

            /**
             * Generate the data that will populate the rendered template.
             *
             * @returns {{showManuscriptName: *, searchType: (field|*), results: *}}
             */
            serializeData: function()
            {
                return {
                    showManuscriptName: this.showManuscriptName,
                    searchType: this.field,
                    results: this.model.getFormattedData()
                };
            },

            onShow: function()
            {
                //var test = new SearchResult("dom%20%20AND%20manuscript:%22CDN-Hsmu%20M2149.L4%22");
                //test.fetch();
                this.resultRegion.show(new SearchResultItemView(this.model, this.field));
                this.paginationRegion.show(this.paginationView);

                GlobalEventHandler.trigger("renderView");
            },

            /**
             * Clear the results object.
             */
            hide: function()
            {
                this.model.clear();
            }
        });
    });
