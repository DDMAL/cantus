//var SearchResult = require(["models/SearchResult"]);
//var CantusAbstractView = require(["views/CantusAbstractView"]);
//var PaginationView = require(["views/PaginationView"]);

define( ['App', 'backbone', 'marionette', 'jquery',
        "models/SearchResult",
        "views/CantusAbstractView",
        "views/PaginationView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $, SearchResult, CantusAbstractView, PaginationView, GlobalEventHandler, template) {

        return CantusAbstractView.extend
        ({
            showManuscriptName: null,
            pageSize: 10,
            currentPage: null,
            paginationView: null,
            query: null,
            field: null,

            initialize: function(options)
            {
                _.bindAll(this, 'render', 'updatePage', 'changeQuery',
                    'updatePaginationView', 'registerClickEvents',
                    'buttonClickCallback');
                this.template = _.template($('#search-result-template').html());
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

                // Query the search result
                this.model.fetch({success: this.updatePaginationView});
                this.listenTo(this.model, 'sync', this.registerClickEvents);
                this.listenTo(this.model, 'sync', this.render);
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

            buttonClickCallback: function(input)
            {
                // Stop the page from auto-reloading
                event.preventDefault();
                // Figure out which button was clicked on
                var splitName = input.target.className.split("-");
                var newIndex = parseInt(splitName[splitName.length - 1], 10);
                // Redirect us to the new url!
                app.navigate(this.model.getFormattedData()[newIndex].url,
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
                this.paginationView = new PaginationView(
                    {
                        name: "search",
                        currentPage: this.currentPage,
                        elementCount: this.model.get("numFound"),
                        pageSize: this.pageSize
                    }
                );
                this.listenTo(this.paginationView, 'change', this.updatePage);
            },

            /**
             * Grab the page number from the paginator
             */
            updatePage: function()
            {
                // Grab the page
                this.currentPage = this.paginationView.getPage();
                // Rebuild the model with a modified query
                this.model.setQuery(this.query + "&start=" + (this.pageSize * (this.currentPage - 1)));
                this.model.fetch();
            },

            render: function()
            {
                // Only render if the model is defined
                if (this.model !== undefined)
                {
                    console.log("Showmanuscriptname: ", this.showManuscriptName);
                    $(this.el).html(this.template(
                        {
                            showManuscriptName: this.showManuscriptName,
                            searchType: this.field,
                            results: this.model.getFormattedData()
                        }
                    ));
                    if (this.model.getFormattedData().length !== 0 && this.paginationView !== null)
                    {
                        this.assign(this.paginationView, this.$el.selector + " .pagination");
                    }
                }
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            },

            hide: function()
            {
                $(this.el).html(this.template({results: []}));
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });
