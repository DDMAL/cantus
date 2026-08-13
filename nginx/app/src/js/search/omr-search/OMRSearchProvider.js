import _ from "underscore";
import Backbone from "backbone";
import Marionette from "marionette";
import Radio from "backbone.radio";

import SearchNotationResultCollection from "collections/SearchNotationResultCollection";
import IncrementalClientSideLoader from "utils/IncrementalClientSideLoader";

import SearchResultHeadingView from "../SearchResultHeadingView";
import NeumeGalleryView from "./NeumeGalleryView";
import ContourChoiceView from "./ContourChoiceView";
import IntervalChoiceView from "./IntervalChoiceView";
import InputView from "./InputView";
import ResultView from "./ResultView";

var manuscriptChannel = Radio.channel('manuscript');

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
                    type: 'neume_names'
                }
            ]
        },
        {
            name: 'pitch-search',
            fields: [
                {
                    name: 'Pitch',
                    type: 'pitch_names'
                },
                {
                    name: 'Pitch (invariant)',
                    type: 'pitch_names_invariant'
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

        this.manuscript = manuscriptModel.get('id');
        this.neumeExemplars = new Backbone.Collection(manuscriptModel.get('neume_exemplars'));

        this.fields = [];

        _.forEach(this.searchPlugins, function (plugin)
        {
            if (manuscriptModel.isPluginActivated(plugin.name))
                this.fields.push.apply(this.fields, plugin.fields);
        }, this);

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

    getDivaAdapter: function ()
    {
        return manuscriptChannel.request('diva');
    },

    resultFetchCallback: function()
    {
        var divaAdapter = this.getDivaAdapter();
        if (!divaAdapter)
            return;

        divaAdapter.setHighlights(_.flatten(this.results.map(function (model)
        {
            return _.map(model.get('boxes'), _.clone);
        })));

        if (this.results.length > 0)
            this.zoomToResult(this.results.at(0));
    },

    /** Stop displaying Diva highlights */
    clearDivaBoxes: function ()
    {
        var divaAdapter = this.getDivaAdapter();
        // If we pass an empty array, then all highlights are erased.
        if (divaAdapter)
            divaAdapter.setHighlights([]);
    },

    zoomToResult: function(model)
    {
        var divaAdapter = this.getDivaAdapter();
        if (!divaAdapter)
            return;

        var box = model.get('boxes')[0];
        if (!box)
            return;

        divaAdapter.focusRegion({
            imageURI: box.p,
            x: box.x,
            y: box.y,
            width: box.w,
            height: box.h
        });
    },

    serializeData: function()
    {
        return {
            searchFields: this.fields
        };
    },

    getSearchMetadata: function ()
    {
        var numFound = this.results.numFound || 0;
        return {
            fieldName: this.field.name,
            query: this.query,
            displayedQuery: this.query,
            numFound: numFound
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
        if (field.type === 'neume_names' && this.neumeExemplars.length > 0)
        {
            var gallery = new NeumeGalleryView({
                collection: this.neumeExemplars
            });

            inputView.listenTo(gallery, 'use:neume', function(newQuery)
            {
                inputView.insertSearchString(newQuery, true);
            });
            regions.searchHelper.show(gallery);
        }
        else if (field.type === 'contour')
        {
            var contourChoices = new ContourChoiceView();
            inputView.listenTo(contourChoices, 'use:contour', function(newQuery)
            {
                inputView.insertSearchString(newQuery, true);
            });
            regions.searchHelper.show(contourChoices);
        }
        else if (field.type === 'intervals'){
            var intervalChoices = new IntervalChoiceView();
            inputView.listenTo(intervalChoices, 'use:interval', function(newQuery)
            {
                inputView.insertSearchString(newQuery, true);
            });
            regions.searchHelper.show(intervalChoices);
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
