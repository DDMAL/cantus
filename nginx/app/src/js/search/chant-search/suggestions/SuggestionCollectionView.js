import _ from 'underscore';
import $ from 'jquery';
import Marionette from 'marionette';

import SuggestionView from './SuggestionView';

export default Marionette.CollectionView.extend({
    tagName: 'div',
    className: 'list-group',

    childView: SuggestionView,

    events: {
        'mousedown': 'suggestionClicked',
        'touchstart': 'suggestionClicked' // Touch support
    },

    initialize: function () {
        _.bindAll(this, 'show', 'hide', 'keyDown');
        this.hide(); // Hide the suggestions initially
    },

    suggestionClicked: function (e) {
        // Triggers "setQuery" in the SearchInputView through the ChantSearchProvider
        var el = $(e.target).closest('a.list-group-item');

        this._setActive(el);
        this._searchActiveSuggestion();
    },

    _setActive: function (el) {
        this.$('.active').removeClass('active');
        el.addClass('active');
    },

    _searchActiveSuggestion: function () {
        // Get the active suggestion
        var el = this.$('.active');
        // Add boolean operator 'AND' between all words, in order to match exactly the suggestion
        var text = `"${el.text()}"`
        this.trigger('click:suggestion', null, text);
        this.hide();
    },

    show: function () {
        this.$el.show();
    },

    hide: function () {
        this.$el.hide();
    },

    keyDown: function (keyCode) {
        this.show(); // Make sure the suggestions are shown when typing

        var el;
        switch (keyCode) {
            // Enter key
            case 13:
                this._searchActiveSuggestion();
                break;

            // Up arrow
            case 38:
                el = this.$('.active').prev();
                if (el.length)
                    this._setActive(el);
                else
                    this._setActive(this.$('a.list-group-item:last'));
                break;

            // Down arrow
            case 40:
                el = this.$('.active').next();
                if (el.length)
                    this._setActive(el);
                else
                    this._setActive(this.$('a.list-group-item:first'));
                break;
        }
    }
});
