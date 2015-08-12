define(["underscore", "marionette"],
    function(_, Marionette)
    {
        "use strict";

        /** Control an input for a search field. Takes a SearchInput model. */
        return Marionette.ItemView.extend({
            template: '#search-input-template',

            events: {
                "submit": "preventSubmit",
                "change .search-input": "setQuery",
                "input .search-input": "setQueryDebounced",
                "keydown .search-input": "updateQueryInput"
            },

            ui: {
                searchInput: '.search-input'
            },

            initialize: function ()
            {
                _.bindAll(this, 'setQuery');

                this.setQueryDebounced = _.debounce(this.setQuery, 250);
            },

            /** We don't need to do anything real on a submit because the query is set on each change. */
            preventSubmit: function (event)
            {
                event.preventDefault();
            },

            setQuery: function ()
            {
                this.model.set('query', this.ui.searchInput.val());
                this.updateQueryInput();
            },

            /**
             * Update the `search-text-entered` class on the query input when that input changes.
             */
            updateQueryInput: function ()
            {
                if (this.model.get('query'))
                {
                    this.ui.searchInput.addClass('search-text-entered');
                }
                else
                {
                    this.ui.searchInput.removeClass('search-text-entered');
                }
            },

            onRender: function ()
            {
                // Set dynamic classes on the query input
                this.updateQueryInput();
            }
        });
    }
);
