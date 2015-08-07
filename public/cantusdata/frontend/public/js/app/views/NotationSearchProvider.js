define([
    "underscore",
    "backbone",
    "marionette",
    "collections/SearchNotationResultCollection",
    "views/NeumeGalleryView",
    "views/SearchNotationInputView",
    "views/SearchResultHeadingView",
    "views/SearchNotationResultView"
], function (
    _,
    Backbone,
    Marionette,
    SearchNotationResultCollection,
    NeumeGalleryView,
    SearchNotationInputView,
    SearchResultHeadingView,
    SearchNotationResultView)
{
    "use strict";

    /**
     * Provide support for searching OMR data via the search interface. See SearchView
     * for a description of the contract this class fulfills.
     */
    return Marionette.Object.extend({
        description: 'Music search',

        results: null,
        divaView: null,
        manuscript: undefined,

        /**
         * Give a list of fields supported given the available search plugins
         */
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

        initialize: function(options)
        {
            _.bindAll(this, 'resultFetchCallback', 'zoomToResult', 'getSearchMetadata');

            // The diva view which we will act upon!
            this.divaView = options.divaView;

            this.neumeExemplars = new Backbone.Collection();

            this.fields = [];

            this.results = new SearchNotationResultCollection();
            this.listenTo(this.results, "sync", this.resultFetchCallback);
        },

        setManuscript: function(model)
        {
            this.manuscript = model.get('siglum_slug');

            this.neumeExemplars.reset(model.get('neume_exemplars'));

            this.fields.splice(this.fields.length);

            _.forEach(this.searchPlugins, function (plugin)
            {
                if (model.isPluginActivated(plugin.name))
                {
                    this.fields.push.apply(this.fields, plugin.fields);
                }
            }, this);
        },

        executeSearch: function (query)
        {
            this.query = query;

            // If we pass an empty array, then all boxes are erased.
            this.divaView.paintBoxes([]);

            // Handle the empty case
            if (!this.query)
            {
                this.results.reset(null);
            }
            else
            {
                this.results.updateParameters({
                    field: this.field.type,
                    fieldName: this.field.name,
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
                searchFields: this.fields
            };
        },

        getSearchMetadata: function ()
        {
            return {
                fieldName: this.results.parameters.fieldName,
                query: this.query
            };
        },

        display: function(field, regions)
        {
            this.field = field;
            this.results.reset();

            // Input
            var inputView = new SearchNotationInputView();

            this.listenTo(inputView, 'search', this.executeSearch);

            regions.searchInput.show(inputView);

            // Neume gallery
            if (field.type === 'neumes' && this.neumeExemplars.length > 0)
            {
                var gallery = new NeumeGalleryView({
                    collection: this.neumeExemplars
                });

                inputView.listenTo(gallery, 'use:neume', inputView.insertSearchString);
                regions.searchHelper.show(gallery);
            }
            else
            {
                regions.searchHelper.empty();
            }

            // Result heading
            regions.searchResultHeading.show(new SearchResultHeadingView({
                collection: this.results,
                showLoading: true,
                getSearchMetadata: this.getSearchMetadata
            }));

            // Results
            var resultView = new SearchNotationResultView({
                collection: this.results
            });

            this.listenTo(resultView, 'zoomToResult', this.zoomToResult);

            regions.searchResults.show(resultView);
        },

        onDestroy: function ()
        {
            this.stopListening();
        }
    });
});
