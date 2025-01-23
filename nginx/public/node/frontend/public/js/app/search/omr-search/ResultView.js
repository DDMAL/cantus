import _ from "underscore";
import Marionette from "marionette";

import lastChildVisible from "utils/lastChildVisible";

import ResultItemView from "./ResultItemView";

import template from './result-list.template.html';

export default Marionette.CollectionView.extend({
    template,
    tagName: 'div',
    className: 'propagate-height',

    childView: ResultItemView,

    childViewContainer: 'tbody',

    collectionEvents: {
        'reset sync': 'updateTable',
        request: 'handleRequest'
    },

    ui: {
        tableWrapper: '.result-table-wrapper',
        table: 'table'
    },

    childEvents: function () {
        return {
            showResult: this.triggerZoomToResult
        };
    },

    initialize: function () {
        this._handleScroll = _.throttle(_.bind(this._loadResultsIfAtEnd, this), 250);
    },

    updateTable: function () {
        if (this.collection.length) {
            this.ui.tableWrapper.show();
        }
        else {
            this.ui.tableWrapper.hide();
        }
    },

    handleRequest: function () {
        this.ui.tableWrapper.hide();
    },

    triggerZoomToResult: function (view) {
        this.trigger('zoomToResult', view.model);
    },

    onRender: function () {
        this.updateTable();

        // We can't use the events hash for this because it relies on events
        // bubbling, and the scroll event does not bubble
        this.ui.tableWrapper.on('scroll', this._handleScroll);
    },

    /**
     * If the last item in the results list is scrolled into view, then request more items
     * @private
     */
    _loadResultsIfAtEnd: function () {
        if (lastChildVisible(this, this.ui.tableWrapper))
            this.trigger('continue:loading');
    }
});
