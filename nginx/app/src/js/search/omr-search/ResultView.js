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

    childViewEvents: {
        showResult: 'triggerZoomToResult'
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

    triggerZoomToResult: function (model) {
        this.trigger('zoomToResult', model);
    },

    onRender: function () {
        this.updateTable();

        // We can't use the events hash for this because it relies on events
        // bubbling, and the scroll event does not bubble
        this.ui.tableWrapper.on('scroll', this._handleScroll);

        // On a tall screen the first rows may not fill the panel, leaving
        // nothing to scroll, so also check whenever the list changes size. Do
        // it on the next frame, or the browser logs a ResizeObserver error.
        this._resizeObserver = new ResizeObserver(() => requestAnimationFrame(() => this._loadResultsIfAtEnd()));
        this._resizeObserver.observe(this.ui.tableWrapper[0]);
    },

    onDestroy: function () {
        this._resizeObserver.disconnect();
    },

    /**
     * If the last item in the results list is scrolled into view, then request more items
     * @private
     */
    _loadResultsIfAtEnd: function () {
        // A queued frame or throttled scroll call can run after the view is
        // destroyed, when this.ui holds selectors instead of elements.
        if (this.isDestroyed())
            return;

        // A hidden list reports every row as in view, which would load them all.
        if (this.ui.tableWrapper.is(':visible') && lastChildVisible(this, this.ui.tableWrapper))
            this.trigger('continue:loading');
    }
});
