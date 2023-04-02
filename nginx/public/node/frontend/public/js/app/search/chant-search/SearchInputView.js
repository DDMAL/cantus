import _ from "underscore";
import Marionette from "marionette";

import template from './search-input.template.html';

/** Control an input for a search field, firing a `search` event when the query changes.
 * Takes a SearchInput model. */
export default Marionette.ItemView.extend({
    template,

    events: {
        "submit": "preventSubmit",
        "change .search-input": "setQuery",
        "input .search-input": "setQueryDebounced",
        "keydown .search-input": "updateQueryInput"
    },

    triggers: {
        "blur .search-input": "blur:input",
        "focus .search-input": "focus:input"
    },

    ui: {
        searchInput: '.search-input'
    },

    initialize: function ()
    {
        _.bindAll(this, 'setQuery');

        this.setQueryDebounced = _.debounce(this.setQuery, 250);

        // Create a regex that will match all invalid volpiano
        // characters
        this.invalidVolpianoRegex = new RegExp('[^1-9a-sw-zA-SW-Z-\(\)]', 'g')
    },

    /** We don't need to do anything real on a submit because the query is set on each change. */
    preventSubmit: function (event)
    {
        event.preventDefault();
    },

    setQuery: function (e, query)
    {
        //If a query is passed, update the value of the text field
        if (query)
            this.ui.searchInput.val(query);

        // For volpiano searches, remove the clef from the search before execution
        var searchField = this.model.get('field');
        var searchInput = this.ui.searchInput.val();
        if (searchField === 'volpiano' || searchField === 'volpiano_literal'){
            if (searchInput == "" || searchInput == "1"){
                this.ui.searchInput.val("1-");
                searchInput = "1-";
            }
            searchInput = searchInput.replaceAll(this.invalidVolpianoRegex, "")
            this.ui.searchInput.val(searchInput)
            searchInput = searchInput.replaceAll("1-","");
            searchInput = searchInput.replaceAll("-","\\-");
        }
        // FIXME(wabain): While this class needs to take a SearchInput model so it can initially
        // be rendered, we're not actually updating that model here - we're just triggering
        // an event which will cause the appropriate changes to propagate. That's kind of
        // confusing.
        this.trigger('search', searchInput);
        this.updateQueryInput();
    },

    /**
     * Update the `search-text-entered` class on the query input when that input changes.
     */
    updateQueryInput: function (e)
    {
        if (this.ui.searchInput.val())
        {
            this.ui.searchInput.addClass('search-text-entered');
        }
        else
        {
            this.ui.searchInput.removeClass('search-text-entered');
        }

        // Send the keycode to the SuggestionCollectionView
        if (e)
            this.trigger('keydown:input', e.keyCode);
    },

    onRender: function ()
    {
        // Set dynamic classes on the query input
        this.updateQueryInput();
    }
});
