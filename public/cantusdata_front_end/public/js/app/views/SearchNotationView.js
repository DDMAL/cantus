//var CantusAbstractModel = require(["models/SearchResult"]);
//var CantusAbstractView = require(["views/CantusAbstractView"]);
//var PaginationView = require(["views/PaginationView"]);

define( ['App', 'backbone', 'marionette', 'jquery',
        "models/SearchResult",
        "views/CantusAbstractView",
        "views/PaginationView"],
    function(App, Backbone, Marionette, $, SearchResult, CantusAbstractView, PaginationView, template) {

        /**
         * Provide an alert message to the user.
         */
        return CantusAbstractView.extend
        ({
            query: null,
            field: null,

            results: null,
            divaView: null,
            paginator: null,
            manuscript: undefined,

            initialize: function(options)
            {
                _.bindAll(this, 'render', 'registerEvents', 'newSearch',
                    'resultFetchCallback', 'zoomToResult');
                this.template = _.template($('#search-notation-template').html());
                // The diva view which we will act upon!
                this.divaView = options.divaView;
                this.results = new CantusAbstractModel();
                this.paginator = new PaginationView({name: "notation-paginator"});
                this.registerEvents();
                this.listenTo(this.results, "sync", this.resultFetchCallback);
            },

            remove: function()
            {
                this.query = null;
                this.results = null;
                this.paginator.remove();
                // We don't actually need to call remove() on this again
                this.divaView = null;
                this.paginator = null;
                this.manuscript = null;
                // Deal with the event listeners
                this.stopListening();
                this.undelegateEvents();
            },

            setManuscript: function(manuscript)
            {
                this.manuscript = manuscript;
            },

            /**
             * Register the events that are necessary to have search input.
             */
            registerEvents: function()
            {
                // Clear out the events
                this.events = {};
                // Register them
                this.events.submit = "newSearch";
                // Delegate the new events
                this.delegateEvents();
            },

            newSearch: function()
            {
                // Stop the page from auto-reloading
                event.preventDefault();
                // Grab the query
                this.query  = encodeURIComponent($(this.$el.selector + ' .query-input').val());
                // Handle the empty case
                if (this.query  === "")
                {
                    // If we pass an empty array, then all boxes are erased.
                    this.divaView.paintBoxes([]);
                    this.clearResults("<h4>Please enter a search query.</h4>");
                }
                else
                {
                    // Grab the field name
                    this.field = encodeURIComponent($(this.$el.selector + ' .search-field').val());
                    this.results.url = siteUrl + "notation-search/?q=" + this.query + "&type=" + this.field + "&manuscript=" + this.manuscript;
                    this.results.fetch();
                }
            },

            resultFetchCallback: function()
            {
                this.divaView.paintBoxes(this.results.get("results"));
                // We need a new paginator
                this.paginator = new PaginationView(
                    {
                        name: "notation-paginator",
                        currentPage: 1,
                        elementCount: this.results.get("numFound"),
                        pageSize: 1
                    }
                );
                // Automatically go to the first result
                this.zoomToResult();
                this.listenTo(this.paginator, 'change', this.zoomToResult);

                this.renderResults();
            },

            zoomToResult: function()
            {
                var newIndex = this.paginator.getPage() - 1;
                this.divaView.zoomToLocation(this.results.get("results")[newIndex]);
            },

            render: function() {
                $(this.el).html(this.template());
            },

            clearResults: function(message)
            {
                $(this.$el.selector + ' .note-search-results').html(
                    message
                );
                $(this.$el.selector + ' .note-pagination').empty();
            },

            renderResults: function()
            {
                $(this.$el.selector + ' .note-search-results').html(
                        "<h4>" + this.results.get("numFound") +
                        ' results found for query "' + this.field + ':' + decodeURIComponent(this.query) + '"</h4>'
                );
                this.assign(this.paginator, this.$el.selector + ' .note-pagination');
            }
        });
    });