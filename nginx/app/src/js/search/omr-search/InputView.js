import Marionette from "marionette";

import template from './input.template.html';

/**
 * Handle the search box for notation search
 */
export default Marionette.View.extend({
    template,

    ui: {
        form: "form",
        searchBox: ".query-input"
    },

    events: {
        'submit @ui.form': 'triggerSearch',
        'input @ui.searchBox': 'clearSearchIfEmpty'
    },

    serializeData: function () {
        return {
            initialQuery: this.getOption('initialQuery')
        };
    },

    /** Trigger a search event when the search form is submitted */
    triggerSearch: function (event) {
        event.preventDefault();
        this.trigger('search', this.ui.searchBox.val());
    },

    /**
     * Clear the results once the search box is emptied, including by the
     * browser's clear button, as chant search does. Other edits still wait
     * for a submit.
     */
    clearSearchIfEmpty: function () {
        if (!this.ui.searchBox.val())
            this.trigger('search', '');
    },

    /** Insert a string into the search input at the current caret position */
    insertSearchString: function (newQuery, addSpace) {
        var input = this.ui.searchBox[0];
        var text = this.ui.searchBox.val();

        // If the HTML5 input selection functions aren't available, just dump
        // the query onto the end of the text
        if (!input.setRangeText) {
            // Place a space before the new term if the existing input
            // ends with a non-space character
            if (addSpace && text.length > 0 && !/\s/.test(text.charAt(text.length - 1)))
                text += ' ' + newQuery;
            else
                text += newQuery;

            this.ui.searchBox.val(text);
            return;
        }

        var selStart = input.selectionStart;
        var selEnd = input.selectionEnd;

        // If a range of text is selected, just replace it
        if (selStart !== selEnd) {
            input.setRangeText(newQuery, selStart, selEnd, 'select');
            return;
        }

        // Place a space before the new term if the existing input
        // ends with a non-space character
        if (addSpace) {
            var prevChar = text.charAt(selStart - 1);
            if (prevChar && !/\s/.test(prevChar))
                newQuery = ' ' + newQuery;

            var nextChar = text.charAt(selStart + 1);
            if (nextChar && !/\s/.test(nextChar))
                newQuery += ' ';
        }

        input.setRangeText(newQuery, selStart, selStart);

        // Set the selection in the input box to the end of what we just inserted
        input.setSelectionRange(selStart + newQuery.length, selStart + newQuery.length);
    }
});
