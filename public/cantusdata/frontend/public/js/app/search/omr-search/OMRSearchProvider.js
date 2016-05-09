import _ from "underscore";
import Backbone from "backbone";
import Marionette from "marionette";

import SearchNotationResultCollection from "collections/SearchNotationResultCollection";
import IncrementalClientSideLoader from "utils/IncrementalClientSideLoader";

import SearchResultHeadingView from "../SearchResultHeadingView";
import NeumeGalleryView from "./NeumeGalleryView";
import InputView from "./InputView";
import ResultView from "./ResultView";

/**
 * Provide support for searching OMR data via the search interface. Required
 * initialization parameters:
 *
 *  - `manuscript`: the manuscript model to initialize with
 *
 * See SearchView for a further description of the contract this class fulfills.
 */
export default Marionette.Object.extend({
    description: 'OMR Search',

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

        var manuscriptModel = options.manuscript;

        this.manuscript = manuscriptModel.get('siglum_slug');
        this.neumeExemplars = new Backbone.Collection(manuscriptModel.get('neume_exemplars'));

        this.fields = [];

        _.forEach(this.searchPlugins, function (plugin)
        {
            if (manuscriptModel.isPluginActivated(plugin.name))
                this.fields.push.apply(this.fields, plugin.fields);
        }, this);

        // The diva view which we will act upon!
        this.divaView = options.divaView;

        this.results = new SearchNotationResultCollection();
        this.displayedResults = new SearchNotationResultCollection();
        this.resultLoadingHandler = new IncrementalClientSideLoader(this.displayedResults, this.results);

        this.listenTo(this.results, "sync", this.resultFetchCallback);
    },

    onSearch: function (query)
    {
        this.query = query;

        this.clearDivaBoxes();

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

            this.resultLoadingHandler.fetch();
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

    /** Stop displaying Diva boxes */
    clearDivaBoxes: function ()
    {
        // If we pass an empty array, then all boxes are erased.
        this.divaView.paintBoxes([]);
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
            fieldName: this.field.name,
            query: this.query
        };
    },

    display: function(field, query, regions)
    {
        this.field = field;
        this.query = query;
        this.results.reset();

        // Input
        var inputView = new InputView({initialQuery: this.query});
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
        var resultView = new ResultView({
            collection: this.displayedResults
        });

        this.listenTo(resultView, 'continue:loading', this._continueLoadingResults);
        this.listenTo(resultView, 'zoomToResult', this.zoomToResult);

        // Clear results from Diva when the results are no longer displayed
        this.listenTo(resultView, 'destroy', this.clearDivaBoxes);

        regions.searchResults.show(resultView);

        // Trigger initial search
        if (this.query)
            this.triggerMethod('search', query);
    },

    /**
     * Display more search results if they are available
     *
     * @private
     */
    _continueLoadingResults: function ()
    {
        this.resultLoadingHandler.continueLoading();
    },

    onDestroy: function ()
    {
        this.stopListening();
    }
});
