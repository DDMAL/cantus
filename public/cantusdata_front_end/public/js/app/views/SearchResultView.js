define( ['App', 'backbone', 'marionette', 'jquery',
        "collections/SearchResultCollection",
        "views/CantusAbstractView",
        "views/PaginationView",
        "views/collection_views/SearchResultCollectionView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             SearchResultCollection,
             CantusAbstractView,
             PaginationView,
             SearchResultCollectionView,
             GlobalEventHandler) {

        return Marionette.LayoutView.extend({
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
                this.collection = new SearchResultCollection();

                if (options.query !== undefined)
                {
                    this.collection.setQuery(options.query);
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
                this.collection.fetch({success: this.updatePaginationView});
                this.listenTo(this.collection, 'sync', this.registerClickEvents);
                this.listenTo(this.paginationView, 'change', this.updatePage);
            },

            /**
             * Register the events for clicking on a search result.
             */
            registerClickEvents: function()
            {
                // FIXME(wabain): this is wrong on so many levels

                // Clear out the events
                this.events = {};
                // Menu items
                for (var i = 0; i < this.collection.length; i++)
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
                Backbone.history.navigate(this.collection.get(newIndex).getFormattedData().url,
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
                this.collection.setQuery(query);
                this.collection.setType(field);
                this.query = String(query);
                this.field = String(field);
                this.collection.fetch({success: this.updatePaginationView});
            },

            /**
             * Rebuild the pagination view with the latest data from the model.
             */
            updatePaginationView: function()
            {
                // Update the paginator parameters.
                this.paginationView.setParams(
                    this.collection.metadata ? this.collection.metadata.numFound : 0,
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
                this.collection.setQuery(this.query + "&start=" + (this.pageSize * (Math.max(this.currentPage - 1,0))));
                this.collection.fetch();
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
                    results: this.collection.map(function (model) {
                        return model.getFormattedData();
                    })
                };
            },

            onShow: function()
            {
                //var test = new SearchResult("dom%20%20AND%20manuscript:%22CDN-Hsmu%20M2149.L4%22");
                //test.fetch();
                this.resultRegion.show(new SearchResultCollectionView({
                    collection: this.collection,
                    searchField: this.field,
                    showManuscriptName: this.showManuscriptName
                }));
                this.paginationRegion.show(this.paginationView);

                GlobalEventHandler.trigger("renderView");
            },

            /**
             * Clear the results object.
             */
            hide: function()
            {
                this.collection.set([]);
            }
        });
    });
