define(["underscore", "marionette"],
    function(_, Marionette)
    {
        "use strict";

        /** Control an input for a search field. Takes a SearchInput model. */
        return Marionette.ItemView.extend({
            template: '#search-input-template',

            modelEvents: {
                'change:field': 'updateFieldInput',
                'change:query': 'updateQueryInput'
            },

            events: {
                "change .search-field": "setField",
                "change .search-input": "setQuery",
                "input .search-input": "setQueryDebounced",
                "keydown .search-input": "updateQueryInput"
            },

            ui: {
                searchInput: '.search-input',
                searchField: '.search-field'
            },

            initialize: function ()
            {
                _.bindAll(this, 'setField', 'setQuery');

                this.cachedQueries = {};

                this.setQueryDebounced = _.debounce(this.setQuery, 250);
            },

            setQuery: function ()
            {
                this.model.set('query', this.ui.searchInput.val());
            },

            setField: function ()
            {
                this.model.set('field', this.ui.searchField.val());
            },

            /**
             * Update the kind of input displayed when the field value changes. Currently, this
             * entails re-rendering the view when the field goes to or from mode and changing
             * the field class on the input element otherwise.
             */
            updateFieldInput: function ()
            {
                var field = this.model.get('field'),
                    prev = this.model.previous('field');

                // Store the old field value
                this.cachedQueries[prev] = this.ui.searchInput.val();

                // Restore the value for the new field
                var cachedQuery = this.cachedQueries[field] || '';
                this.model.set('query', cachedQuery);

                if (this.requiresRerender(field) || this.requiresRerender(prev))
                {
                    this.render();
                }
                else
                {
                    this.ui.searchInput.removeClass('field-' + prev).addClass('field-' + field);
                }

                // FIXME(wabain): setting this manually is pretty fragile
                // Really, things should be organized s.t. the search input value is always
                // the same as the model value without needing this to be a special case
                this.ui.searchInput.val(cachedQuery);
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

            /**
             * Return whether a change to or from the given search field should trigger a
             * re-render
             *
             * @param fieldType
             * @returns {boolean}
             */
            requiresRerender: function (fieldType)
            {
                return fieldType === 'mode';
            },

            onRender: function ()
            {
                // Set the search field
                this.ui.searchField.val(this.model.get('field'));

                // Set dynamic classes on the query input
                this.updateQueryInput();
            }
        });
    }
);
