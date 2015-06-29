define(["marionette"],
    function(Marionette)
    {
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

                if (this.requiresRerender(field) || this.requiresRerender(prev))
                {
                    this.render();
                }
                else
                {
                    this.ui.searchInput.removeClass('field-' + prev).addClass('field-' + field);
                }
            },

            /**
             * Update the `search-text-entered` class on the query input when that input changes.
             */
            updateQueryInput: function ()
            {
                if (this.ui.searchInput.val())
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
            }
        });
    }
);
