define(["underscore",
        "backbone",
        "marionette",
        "collections/SearchNotationResultCollection",
        "views/SearchNotationResultView",
        "views/SearchResultHeadingView",
        "views/NeumeGalleryView"],
function(_,
         Backbone,
         Marionette,
         SearchNotationResultCollection,
         SearchNotationResultView,
         SearchResultHeadingView,
         NeumeGalleryView)
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

        searchPlugins: [
            {
                name: 'neume-search',
                fields: [
                    {
                        name: 'Neume',
                        type: 'neumes'
                    }
                ]
            },
            {
                name: 'pitch-search',
                fields: [
                    {
                        name: 'Pitch',
                        type: 'pnames'
                    },
                    {
                        name: 'Pitch (invariant)',
                        type: 'pnames-invariant'
                    },
                    {
                        name: 'Contour',
                        type: 'contour'
                    },
                    {
                        name: 'Interval',
                        type: 'intervals'
                    }
                ]
            }
        ],

        ui: {
            typeSelector: ".search-field",
            searchBox: ".query-input"
        },

        events: {
            submit: 'newSearch'
        },

        triggers: {
            'change @ui.typeSelector': 'search:type:selected'
        },

        regions: {
            neumeGallery: '.neume-gallery',
            resultHeading: ".result-heading",
            searchResults: ".note-search-results",
            glyphTypesRegion: ".glyph-types"
        },

        initialize: function(options)
        {
            _.bindAll(this, 'newSearch', 'resultFetchCallback', 'zoomToResult', 'getSearchMetadata');

            // The diva view which we will act upon!
            this.divaView = options.divaView;

            this.neumeExemplars = new Backbone.Collection();

            this.searchFields = [];

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

        /**
         * Configure the view for the current search type
         */
        onSearchTypeSelected: function ()
        {
            if (this.getSearchType() === 'neumes' && this.neumeExemplars.length > 0)
            {
                var gallery = new NeumeGalleryView({
                    collection: this.neumeExemplars
                });

                this.listenTo(gallery, 'use:neume', this.insertSearchString);
                this.neumeGallery.show(gallery);
            }
            else if (this.neumeGallery.currentView)
            {
                this.neumeGallery.empty();
            }
        },

        insertSearchString: function (newQuery)
        {
            var input = this.ui.searchBox[0];
            var text = this.ui.searchBox.val();

            // If the HTML5 input selection functions aren't available, just dump
            // the query onto the end of the text
            if (!input.setRangeText)
            {
                // Place a space before the new term if the existing input
                // ends with a non-space character
                if (text.length > 0 && !/\s/.test(text.charAt(text.length - 1)))
                    text += ' ' + newQuery;
                else
                    text += newQuery;

                this.ui.searchBox.val(text);
                return;
            }

            var selStart = input.selectionStart;
            var selEnd = input.selectionEnd;

            // If a range of text is selected, just replace it
            if (selStart !== selEnd)
            {
                input.setRangeText(newQuery, selStart, selEnd, 'select');
                return;
            }

            // Place a space before the new term if the existing input
            // ends with a non-space character
            var prevChar = text.charAt(selStart - 1);
            if (prevChar && !/\s/.test(prevChar))
                newQuery = ' ' + newQuery;

            var nextChar = text.charAt(selStart + 1);
            if (nextChar && !/\s/.test(nextChar))
                newQuery += ' ';

            input.setRangeText(newQuery, selStart, selStart);

            // Set the selection in the input box to the end of what we just inserted
            input.setSelectionRange(selStart + newQuery.length, selStart + newQuery.length);
        },

        setManuscript: function(model)
        {
            this.manuscript = model.get('siglum_slug');

            this.neumeExemplars.reset(model.get('neume_exemplars'));

            this.searchFields.splice(this.searchFields.length);

            _.forEach(this.searchPlugins, function (plugin)
            {
                if (model.isPluginActivated(plugin.name))
                {
                    this.searchFields.push.apply(this.searchFields, plugin.fields);
                }
            }, this);
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
                // FIXME(wabain): does this need to be an attribute?
                var field = this.field = this.getSearchType();

                var fieldName = _.find(this.searchFields, function (fieldDescription)
                {
                    return fieldDescription.type === field;
                }).name;

                this.results.updateParameters({
                    field: this.field,
                    fieldName: fieldName,
                    query: this.query,
                    manuscript: this.manuscript
                });

                this.results.fetch();
            }
            return false;
        },

        resultFetchCallback: function()
        {
            this.divaView.paintBoxes(_.flatten(this.results.map(function (model)
            {
                return _.map(model.get('boxes'), _.clone);
            })));

            if (this.results.length > 0)
                this.zoomToResult(this.results.at(0));
        },

        zoomToResult: function(model)
        {
            this.divaView.zoomToLocation(_.clone(model.get('boxes')[0]));
        },

        serializeData: function()
        {
            return {
                searchFields: this.searchFields
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

        getSearchMetadata: function ()
        {
            return {
                fieldName: this.results.parameters.fieldName,
                query: decodeURIComponent(this.results.parameters.query)
            };
        },

        onRender: function()
        {
            // Configure the helpers for the current search type
            this.onSearchTypeSelected();

            this.resultHeading.show(new SearchResultHeadingView({
                collection: this.results,
                showLoading: true,
                getSearchMetadata: this.getSearchMetadata
            }));

            var resultView = new SearchNotationResultView({
                collection: this.results
            });

            this.listenTo(resultView, 'zoomToResult', this.zoomToResult);

            this.searchResults.show(resultView);
        }
    });
});