define(['marionette',
        "collections/SearchNotationResultCollection",
        "views/SearchNotationResultView"],
function(Marionette,
         SearchNotationResultCollection,
         SearchNotationResultView)
{
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

        events: {
            submit: 'newSearch'
        },

        regions: {
            glyphTypesRegion: ".glyph-types",
            searchResults: ".note-search-results"
        },

        initialize: function(options)
        {
            _.bindAll(this, 'newSearch', 'resultFetchCallback', 'zoomToResult');
            // The diva view which we will act upon!
            this.divaView = options.divaView;
            this.results = new SearchNotationResultCollection();
            this.listenTo(this.results, "sync", this.resultFetchCallback);
        },

        remove: function()
        {
            this.query = null;
            this.results = null;

            // We don't actually need to call remove() on this again
            this.divaView = null;
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

        newSearch: function(event)
        {
            // Stop the page from auto-reloading
            event.preventDefault();
            // Grab the query
            this.query  = this.getSearchValue();

            // If we pass an empty array, then all boxes are erased.
            this.divaView.paintBoxes([]);

            // Handle the empty case
            if (!this.query)
            {
                this.results.reset(null, {message: 'Please enter a search query.'});
            }
            else
            {
                // Grab the field name
                this.field = this.getSearchType();

                this.results.updateParameters({
                    field: this.field,
                    fieldName: this.searchFields[this.field],
                    query: this.query,
                    manuscript: this.manuscript
                });

                this.results.fetch();
            }
            return false;
        },

        resultFetchCallback: function()
        {
            this.divaView.paintBoxes(this.results.map(function (model)
            {
                return _.clone(model.attributes);
            }));

            if (this.results.length > 0)
                this.zoomToResult(this.results.at(0));
        },

        zoomToResult: function(model)
        {
            this.divaView.zoomToLocation(_.clone(model.attributes));
        },

        serializeData: function()
        {
            // Create an array with the field types
            var searchFieldArray = _.map(this.searchFields, function (name, code)
            {
                return {
                    codeName: code,
                    name: name
                };
            });

            return {
                searchFields: searchFieldArray
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

        onRender: function()
        {
            var resultView = new SearchNotationResultView({
                collection: this.results
            });

            this.listenTo(resultView, 'zoomToResult', this.zoomToResult);

            this.searchResults.show(resultView);
        }
    });
});