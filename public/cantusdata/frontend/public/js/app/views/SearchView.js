define(["underscore", "jquery", "marionette"], function(_, $, Marionette)
{
    "use strict";

    /**
     * Top-level search view. This view delegates to search provider classes
     * to handle most of the actual business logic.
     *
     * Its responsibilities are just
     *
     *  - to render the field selection dropdown,
     *  - to alert the correct provider via the `provider.display` method when the selected field
     *    changes,
     *  - and to trigger the providers' onDestroy method when the view is destroyed.
     */
    return Marionette.LayoutView.extend({
        template: "#search-template",

        showManuscriptName: true,

        regions: {
            searchInput: ".search-input",
            searchHelper: ".search-helper",
            searchResultHeading: ".search-heading",
            searchResults: ".search-results"
        },

        ui: {
            fieldSelectorLabel: '.search-field-selector .dropdown-toggle .field-label',
            fieldSelectorMenuItem: '.search-field-selector .dropdown-menu a'
        },

        events: {
            'click @ui.fieldSelectorMenuItem': 'fieldSelected'
        },

        /**
         * Initialization parameters:
         *
         * - `providers`: an array of search providers to delegate to
         */
        initialize: function ()
        {
            this.providers = this.getOption('providers');
            this.activeProvider = this.providers[0];
            this.activeField = this.activeProvider.fields[0];
        },

        fieldSelected: function (event)
        {
            var menuItem = $(event.target);
            var provider = this.providers[menuItem.data('provider-index')];
            var field = provider.fields[menuItem.data('field-index')];

            if (field !== this.activeField)
            {
                if (provider !== this.activeProvider)
                {
                    this.activeProvider = provider;
                }

                this.activeField = field;
                this.ui.fieldSelectorLabel.text(this.activeField.name);

                this.renderActiveField();
            }
        },

        serializeData: function ()
        {
            return {
                searchProviders: this.providers,
                activeField: this.activeField
            };
        },

        renderActiveField: function ()
        {
            this.activeProvider.display(this.activeField, this.getRegions());
        },

        onRender: function ()
        {
            this.renderActiveField();
        },

        onDestroy: function ()
        {
            _.invoke(this.providers, 'triggerMethod', 'destroy');
        }
    });
});