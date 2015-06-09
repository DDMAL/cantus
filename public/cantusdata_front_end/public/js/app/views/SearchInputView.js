define(["marionette"],
    function(Marionette)
    {
        /** Control an input for a search field. Takes a SearchInput model. */
        return Marionette.ItemView.extend({
            template: '#search-input-template',

            modelEvents: {
                'change:field': 'updateFieldInput'
            },

            events: {
                "change .search-field": "setField",
                "change .search-input": "setQuery",
                "input .search-input": "setQueryDebounced"
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
             * just means re-rendering the view when the field goes to or from mode.
             */
            updateFieldInput: function ()
            {
                if (this.model.get('field') === 'mode' || this.model.previous('field') === 'mode')
                    this.render();
            }
        });
    }
);
