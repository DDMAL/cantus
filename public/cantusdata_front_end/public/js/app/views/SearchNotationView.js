define( ['App', 'backbone', 'marionette', 'jquery',
        "models/CantusAbstractModel",
        "models/SearchResult",
        "views/CantusAbstractView",
        "views/PaginationView",
        "views/collection_views/GlyphTypeCollectionView",
        "config/GlobalVars"],
    function(App, Backbone, Marionette, $,
             CantusAbstractModel,
             SearchResult,
             CantusAbstractView,
             PaginationView,
             GlyphTypeCollectionView,
             GlobalVars) {

"use strict";

/**
 * Provide an alert message to the user.
 */
return Marionette.LayoutView.extend
({
    query: null,
    field: null,

    results: null,
    divaView: null,
    paginator: null,
    manuscript: undefined,

    template: "#search-notation-template",

    searchFields: {
        pnames: "Pitch",
        neumes: "Neume"
    },

    ui: {
        typeSelector: ".search-field",
        searchBox: ".query-input"
    },

    regions: {
        glyphTypesRegion: ".glyph-types",
        paginatorRegion: ".note-pagination"
    },

    initialize: function(options)
    {
        _.bindAll(this, 'registerEvents', 'newSearch',
            'resultFetchCallback', 'zoomToResult');
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
        if (this.paginator !== null) {
            this.paginator.remove();
        }
        // We don't actually need to call remove() on this again
        this.divaView = null;
        this.paginator = null;
        this.manuscript = null;
        // Deal with the event listeners
        this.stopListening();
        this.undelegateEvents();
    },

    getSearchType: function()
    {
        return encodeURIComponent(this.ui.typeSelector.val());
    },

    getSearchValue: function()
    {
        return encodeURIComponent(this.ui.searchBox.val());
    },

    setManuscript: function(manuscript)
    {
        this.manuscript = manuscript;
    },

    /**
     * Set the search fields to display.
     *
     * @param fields
     */
    setSearchFields: function(fields)
    {
        this.searchFields = fields;
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

    newSearch: function(event)
    {
        // Stop the page from auto-reloading
        event.preventDefault();
        // Grab the query
        this.query  = this.getSearchValue();
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
            this.field = this.getSearchType();
            this.results.url = GlobalVars.siteUrl + "notation-search/?q=" + this.query + "&type=" + this.field + "&manuscript=" + this.manuscript;
            this.results.fetch();
        }
        return false;
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

    serializeData: function()
    {
        // Create an array with the field types
        var searchFieldArray = [];
        for (var fieldCode in this.searchFields)
        {
            searchFieldArray.push(
                {
                    codeName: fieldCode,
                    name: this.searchFields[fieldCode]
                }
            );
        }
        return {
            searchFields:searchFieldArray
        };
    },

    //onRender: function()
    //{
    //    // TODO: Implement the search query builder
    //    //var glyphTypes = new Backbone.Collection();
    //    //glyphTypes.add(new Backbone.Model());
    //    //this.glyphTypesRegion.show(new GlyphTypeCollectionView({
    //    //    collection: glyphTypes
    //    //}));
    //},

    clearResults: function(message)
    {
        $(this.$el.selector + ' .note-search-results').html(message);
        $(this.$el.selector + ' .note-pagination').empty();
    },

    renderResults: function()
    {
        $(this.$el.selector + ' .note-search-results').html(
                "<h3>" + this.searchFields[this.field] + " search</h3><h4>" +
                this.results.get("numFound") + ' results found for query "' +
                decodeURIComponent(this.query) + '"</h4>'
        );
        this.paginatorRegion.show(this.paginator);
    }
});
});