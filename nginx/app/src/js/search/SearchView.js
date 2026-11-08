import _ from "underscore";
import $ from "jquery";
import Marionette from "marionette";

import template from './search.template.html';

/**
 * Top-level search view. This view delegates to search provider classes
 * to handle most of the actual business logic.
 *
 * Its responsibilities are just
 *
 *  - to render the field selection dropdown,
 *  - to alert the correct provider via the `provider.display` method when the selected field
 *    changes,
 *  - to trigger the `onSearch` method whenever the input view triggers a search event
 *  - and to trigger the providers' onDestroy method when the view is destroyed.
 *
 * Providers are expected to implement those methods, to provide an array `fields` with field
 * types and names, and to provide a string `description` which describes the search type provided.
 *
 * A field can also have a `variant` ({label, tooltip, type}), shown as a checkbox under the search
 * box. While it is checked, the field searches with the variant's type. The field's input view
 * must implement `getQuery`, so that toggling the checkbox can search with the text in the box.
 *
 *  TODO: Make this API less confusing. As a historical note, it works this way because it merges
 *  two search views which had different implementations. Refactoring those to make the abstraction
 *  better would be nice.
 */
export default Marionette.View.extend({
    template,
    tagName: 'div',
    className: 'propagate-height',

    regions: {
        searchInput: ".search-input",
        searchSuggestions: ".search-suggestions",
        searchHelper: ".search-helper",
        searchResultHeading: ".search-heading",
        searchResults: ".search-results"
    },

    ui: {
        fieldSelectorLabel: '.search-field-selector .dropdown-toggle .field-label',
        fieldSelectorMenuItem: '.search-field-selector .dropdown-menu a',
        variant: '.search-field-variant',
        variantCheckbox: '.search-field-variant input',
        variantLabel: '.search-field-variant label'
    },

    events: {
        'click @ui.fieldSelectorMenuItem': 'fieldSelected',
        'change @ui.variantCheckbox': 'variantToggled'
    },

    /**
     * Initialization parameters:
     *
     * - `providers`: an array of search providers to delegate to
     * - `searchTerm`: the initial search type and query to look for
     */
    initialize: function () {
        this.cachedQueries = {};
        this.checkedVariants = {};

        this.providers = this.getOption('providers');
        this._setInitialSearchTerm();
    },

    /** Match up the passed in search term to a field from the providers,
     * or fall back to the first provider's first field and an empty query.
     * @private
     */
    _setInitialSearchTerm: function () {
        var searchTerm = this.getOption('searchTerm');

        // If a search term was given, try to match its search type to some provider field
        var searchTypeFound;
        if (searchTerm) {
            // Special case (mostly for backwards compatibility): if a search
            // query is provided but not a search type, default to the type "all"
            if (searchTerm.query && !searchTerm.type) {
                searchTerm.type = 'all';
            }

            searchTypeFound = this._findSearchField(searchTerm.type);
        }
        else {
            searchTypeFound = false;
        }

        // If the search type was not found or not given, use the first available
        // search field and an empty query
        if (searchTypeFound) {
            this._setQuery(searchTerm.query);
        }
        else {
            this.activeProvider = this.providers[0];
            this.activeField = this.activeProvider.fields[0];
            this._setQuery('');
        }
    },

    /** Iterate through the providers and their fields to find one
     * with the type `type` or a variant of that type. Set the active
     * provider and field if a match is found, and whether the variant
     * is checked.
     *
     * @param {String} type
     * @returns {Boolean} Whether a match was found
     * @private
     */
    _findSearchField: function (type) {
        return _.some(this.providers, function (provider) {
            return _.some(provider.fields, function (field) {
                var isVariant = !!field.variant && field.variant.type === type;

                if (field.type === type || isVariant) {
                    this.activeProvider = provider;
                    this.activeField = field;
                    this.checkedVariants[field.type] = isVariant;
                    return true;
                }

                return false;
            }, this);
        }, this);
    },

    /** Set both the query and the cached query to a new string.
     * Makes it simpler to set the query in order to avoid forgetting
     * to also set the cachedQueries array
     *
     * @param {String} query
     * @private
     */
    _setQuery: function (query) {
        this.query = this.cachedQueries[this.activeField.type] = query;
    },

    /** The active field, with the variant's type while its variant is checked
     * @private
     */
    _searchedField: function () {
        var field = this.activeField;

        if (field.variant && this.checkedVariants[field.type])
            return { name: field.name, type: field.variant.type };

        return field;
    },

    /** Add a binding to listen for `search` on the input view whenever an
     * input view is shown. */
    bindInputSearchEvent: function (inputView) {
        this.listenTo(inputView, 'search', function (query) {
            this._setQuery(query);

            this.trigger('search', { type: this._searchedField().type, query: query });
            this.activeProvider.triggerMethod('search', query);
        });
    },

    /** Search again with or without the variant, using the text in the search box */
    variantToggled: function () {
        this.checkedVariants[this.activeField.type] = this.ui.variantCheckbox.prop('checked');

        this._setQuery(this.getRegion('searchInput').currentView.getQuery());
        this.renderActiveField();
    },

    fieldSelected: function (event) {
        var menuItem = $(event.target);
        var provider = this.providers[menuItem.data('provider-index')];
        var field = provider.fields[menuItem.data('field-index')];

        if (field !== this.activeField) {
            if (provider !== this.activeProvider) {
                this.activeProvider = provider;
            }

            this.activeField = field;
            this.ui.fieldSelectorLabel.text(this.activeField.name);

            this.query = this.cachedQueries[field.type] || '';

            this.renderActiveField();
        }
    },

    serializeData: function () {
        return {
            searchProviders: this.providers,
            activeField: this.activeField,
            // Unique because a page can have more than one search view
            variantInputId: _.uniqueId('search-field-variant-')
        };
    },

    renderActiveField: function () {
        this._renderVariant();

        var field = this._searchedField();
        this.trigger('search', { type: field.type, query: this.query });
        this.activeProvider.display(field, this.query, this.getRegions());
        this.bindInputSearchEvent(this.getRegion('searchInput').currentView);
    },

    _renderVariant: function () {
        var variant = this.activeField.variant;

        this.ui.variant.prop('hidden', !variant);

        if (variant) {
            this.ui.variant.attr('title', variant.tooltip);
            // Screen readers announce the checkbox's title, not the row's
            this.ui.variantCheckbox.attr('title', variant.tooltip);
            this.ui.variantLabel.text(variant.label);
            this.ui.variantCheckbox.prop('checked', !!this.checkedVariants[this.activeField.type]);
        }
    },

    onRender: function () {
        this.renderActiveField();
    },

    onDestroy: function () {
        _.invoke(this.providers, 'triggerMethod', 'destroy');
    }
});
