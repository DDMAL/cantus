import Marionette from "marionette";
import SearchView from "search/SearchView";
import ChantSearchProvider from "search/chant-search/ChantSearchProvider";
import fillViewportHeight from "behaviors/FillViewportHeightBehavior";

import template from './search-page.template.html';

/**
 * This page is for searching.
 *
 * @constructor
 */
export default Marionette.View.extend({
    template,
    tagName: 'div',
    className: 'propagate-height',

    behaviors: [fillViewportHeight],

    regions: {
        searchRegion: '#search'
    },

    initialize: function (options) {
        // Initialize the subview
        this.searchView = new SearchView({
            providers: [new ChantSearchProvider({
                additionalResultFields: ['manuscript', 'genre', 'mode', 'feast', 'office', 'position']
            })],
            searchTerm: options.searchTerm
        });
    },

    onRender: function () {
        this.getRegion('searchRegion').show(this.searchView);
    }
});
