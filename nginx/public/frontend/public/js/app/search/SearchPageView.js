import Marionette from "marionette";
import SearchView from "search/SearchView";
import ChantSearchProvider from "search/chant-search/ChantSearchProvider";

import template from './search-page.template.html';

/**
 * This page is for searching.
 *
 * @constructor
 */
export default Marionette.LayoutView.extend({
    template,
    tagName: 'div class="propagate-height"',

    behaviors: {
        fillViewportHeight: true
    },

    regions: {
        searchRegion: '#search'
    },

    // Subviews
    searchView: null,

    initialize: function(options)
    {
        // Initialize the subview
        this.searchView = new SearchView({
            providers: [new ChantSearchProvider({
                additionalResultFields: ['manuscript', 'genre', 'mode', 'feast', 'office', 'position']
            })],
            searchTerm: options.searchTerm
        });
    },

    onRender: function()
    {
        this.searchRegion.show(this.searchView, {preventDestroy: true});
    }
});
