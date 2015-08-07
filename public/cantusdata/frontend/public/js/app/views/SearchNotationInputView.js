define([
    "marionette"
],
function (Marionette)
{
    "use strict";

    /**
     * Handle the search box for notation search
     */
    return Marionette.ItemView.extend({
        template: '#search-notation-input-template',

        ui: {
            form: "form",
            searchBox: ".query-input"
        },

        events: {
            'submit @ui.form': 'triggerSearch'
        },

        /** Trigger a search event when the search form is submitted */
        triggerSearch: function (event)
        {
            event.preventDefault();
            this.trigger('search', this.ui.searchBox.val());
        },

        /** Insert a string into the search input at the current caret position */
        insertSearchString: function (newQuery)
        {
            var input = this.ui.searchBox[0];
            var text = this.ui.searchBox.val();

            // If the HTML5 input selection functions aren't available, just dump
            // the query onto the end of the text
            if (!input.setRangeText)
            {
                // Place a space before the new term if the existing input
                // ends with a non-space character
                if (text.length > 0 && !/\s/.test(text.charAt(text.length - 1)))
                    text += ' ' + newQuery;
                else
                    text += newQuery;

                this.ui.searchBox.val(text);
                return;
            }

            var selStart = input.selectionStart;
            var selEnd = input.selectionEnd;

            // If a range of text is selected, just replace it
            if (selStart !== selEnd)
            {
                input.setRangeText(newQuery, selStart, selEnd, 'select');
                return;
            }

            // Place a space before the new term if the existing input
            // ends with a non-space character
            var prevChar = text.charAt(selStart - 1);
            if (prevChar && !/\s/.test(prevChar))
                newQuery = ' ' + newQuery;

            var nextChar = text.charAt(selStart + 1);
            if (nextChar && !/\s/.test(nextChar))
                newQuery += ' ';

            input.setRangeText(newQuery, selStart, selStart);

            // Set the selection in the input box to the end of what we just inserted
            input.setSelectionRange(selStart + newQuery.length, selStart + newQuery.length);
        }
    });
});
