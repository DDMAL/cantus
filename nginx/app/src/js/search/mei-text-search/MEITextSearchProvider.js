import _ from "underscore";
import $ from "jquery";
import Backbone from "backbone";
import Marionette from "marionette";
import Radio from "backbone.radio";

import SearchMEITextResultCollection from "collections/SearchMEITextResultCollection";
import IncrementalClientSideLoader from "utils/IncrementalClientSideLoader";

import SearchResultHeadingView from "../SearchResultHeadingView";
import InputView from "../omr-search/InputView";
import ResultView from "./ResultView";
import template from './text-help.template.html';

var manuscriptChannel = Radio.channel('manuscript');

/** Explain the search and let the user set its options */
var OptionsView = Marionette.View.extend({
    template,

    events: {
        'change [data-option]': function (event) {
            this.model.set($(event.target).data('option'), event.target.checked);
        }
    }
});

/**
 * Provide support for searching the lines of text encoded in a manuscript's
 * MEI files (e.g. OCR'd text), for manuscripts without chant records. Required
 * initialization parameters:
 *
 *  - `manuscript`: the manuscript model to initialize with
 *
 * See SearchView for a further description of the contract this class fulfills.
 */
export default Marionette.Object.extend({
    description: 'Page Text Search',

    fields: [
        {
            name: 'Text',
            type: 'mei_text'
        }
    ],

    initialize: function (options)
    {
        _.bindAll(this, 'resultFetchCallback', 'zoomToResult', 'getSearchMetadata');

        this.manuscript = options.manuscript.get('id');

        this.searchOptions = new Backbone.Model({
            ignoreHyphens: true,
            multiline: false
        });

        this.results = new SearchMEITextResultCollection();
        this.displayedResults = new SearchMEITextResultCollection();
        this.resultLoadingHandler = new IncrementalClientSideLoader(this.displayedResults, this.results);

        this.listenTo(this.results, "sync", this.resultFetchCallback);

        // Rerun the current search with the new options
        this.listenTo(this.searchOptions, 'change', function ()
        {
            this.triggerMethod('search', this.query);
        });
    },

    onSearch: function (query)
    {
        this.query = query;

        this.clearDivaBoxes();

        if (!this.query)
        {
            this.results.reset(null);
        }
        else
        {
            this.results.updateParameters(_.extend({
                query: this.query,
                manuscript: this.manuscript
            }, this.searchOptions.toJSON()));

            this.resultLoadingHandler.fetch();
        }
        return false;
    },

    getDivaAdapter: function ()
    {
        return manuscriptChannel.request('diva');
    },

    resultFetchCallback: function ()
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
        if (divaAdapter)
            divaAdapter.setHighlights([]);
    },

    zoomToResult: function (model)
    {
        var divaAdapter = this.getDivaAdapter();
        if (!divaAdapter)
            return;

        // A result spanning two lines has a box for each; frame both. Both
        // are on the same page.
        var boxes = model.get('boxes');
        if (boxes.length === 0)
            return;

        var left = _.min(_.pluck(boxes, 'x'));
        var top = _.min(_.pluck(boxes, 'y'));
        var right = _.max(_.map(boxes, function (box) { return box.x + box.w; }));
        var bottom = _.max(_.map(boxes, function (box) { return box.y + box.h; }));

        divaAdapter.focusRegion({
            imageURI: boxes[0].p,
            x: left,
            y: top,
            width: right - left,
            height: bottom - top
        });
    },

    getSearchMetadata: function ()
    {
        return {
            fieldName: this.field.name,
            query: this.query,
            displayedQuery: this.query,
            numFound: this.results.numFound || 0
        };
    },

    display: function (field, query, regions)
    {
        this.field = field;
        this.query = query;
        this.results.reset();

        regions.searchInput.show(new InputView({ initialQuery: this.query }));
        regions.searchHelper.show(new OptionsView({ model: this.searchOptions }));

        regions.searchResultHeading.show(new SearchResultHeadingView({
            collection: this.results,
            showLoading: true,
            getSearchMetadata: this.getSearchMetadata
        }));

        var resultView = new ResultView({
            collection: this.displayedResults
        });

        this.listenTo(resultView, 'continue:loading', this._continueLoadingResults);
        this.listenTo(resultView, 'zoomToResult', this.zoomToResult);

        // Clear results from Diva when the results are no longer displayed
        this.listenTo(resultView, 'destroy', this.clearDivaBoxes);

        regions.searchResults.show(resultView);

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
