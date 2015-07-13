define(['underscore', 'jquery', 'marionette', 'views/item_views/SearchResultItemView'],
    function(_, $, Marionette, SearchResultItemView)
    {

        "use strict";

        // TODO(wabain): this is misnamed since it's actually a CompositeView
        // but it should really be merged into the SearchResultView

        // FIXME(wabain): After updating Marionette, get this to use reorderOnSort: true

        /**
         * View representing a Search Result with count.
         */
        return Marionette.CompositeView.extend({
            template: "#search-result-list-template",

            childView: SearchResultItemView,
            childViewContainer: '.child-container',

            showManuscriptName: true,

            collectionEvents: {
                "sync reset": "render",
                "add remove": "hideIfEmpty"
            },

            ui: {
                resultList: '.result-list',
                resultHeading: '.result-list th'
            },

            events: {
                'click @ui.resultHeading': 'changeSortCriterion'
            },

            initialize: function()
            {
                _.bindAll(this, 'hideIfEmpty');

                // FIXME(wabain): update this to use mergeOptions after updating Marionette
                this.searchParameters = this.getOption('searchParameters');
                this.showManuscriptName = this.getOption('showManuscriptName');
            },

            childViewOptions: function ()
            {
                return {
                    searchType: this.searchParameters.get('field'),
                    query: this.searchParameters.get('query'),
                    showManuscriptName: this.showManuscriptName
                };
            },

            onRenderTemplate: function ()
            {
                this.hideIfEmpty();

                // Set the caret on the result table heading which corresponds
                // to the field which is being sorted by
                var sortField = this.searchParameters.get('sortBy');
                _.any(this.ui.resultHeading, _.bind(function (heading)
                {
                    heading = $(heading);

                    if (this.getHeadingSearchField(heading) === sortField)
                    {
                        this.setHeadingCaret(heading);
                        return true;
                    }
                }, this));
            },

            /**
             * If there is no query then hide the view. If there is a
             * query but no results then hide the result table.
             */
            hideIfEmpty: function ()
            {
                // Catch the condition where this is fired before the template has been rendered
                if (!this.$el)
                    return;

                if (!this.searchParameters.get('query'))
                {
                    this.$el.hide();
                }
                else
                {
                    this.$el.show();

                    if (this.collection.length === 0)
                        this.ui.resultList.hide();
                    else
                        this.ui.resultList.show();
                }
            },

            /**
             * When a search header is clicked, change the sort criterion for the results.
             * If the field which the header represents is already the sort criterion, toggle
             * the sort order. Otherwise, sort by the header's criterion in ascending order.
             *
             * @param event
             */
            changeSortCriterion: function (event)
            {
                // It's convenient to listen to the click event when it's bubbled up to the th
                // element, but let's only act if the a element is what was clicked.
                if (event.target.tagName !== 'A')
                    return;

                event.preventDefault();
                event.stopPropagation();

                var heading = $(event.currentTarget);
                var field = this.getHeadingSearchField(heading);

                if (field === this.searchParameters.get('sortBy'))
                {
                    this.searchParameters.set('reverseSort', !this.searchParameters.get('reverseSort'));
                }
                else
                {
                    this.searchParameters.set({sortBy: field, reverseSort: false});
                }

                // FIXME(wabain): we don't need to dynamically change the heading for now because
                // the view is re-rendered on sort. But we'll need this once we upgrade Marionette
                // and can stop the re-rendering.
                //this.setHeadingCaret(heading);
                //this.updateHeadingCaretOnNextChange(heading);
            },

            /**
             * Get the Solr field represented by a search result header cell.
             *
             * @param heading
             * @returns {string}
             */
            getHeadingSearchField: function (heading)
            {
                return heading.attr('data-sort-field') || heading.children('a').text().toLowerCase();
            },

            /**
             * Update the caret representing the sort ordering on the result table heading which
             * corresponds to the field which is being sorted by.
             *
             * @param heading The heading for the active row
             */
            setHeadingCaret: function (heading)
            {
                heading.children('.search-caret')
                    .addClass(this.searchParameters.get('reverseSort') ? 'caret caret-reversed' : 'caret');
            },

            /**
             * Register callbacks to change the state of the heading for the sorted field the next time that
             * the sort criteria change.
             *
             * NOTE: this isn't used at the moment because the whole view is re-rendered when the search
             * sorting changes.
             *
             * @param heading
             */
            updateHeadingCaretOnNextChange: function (heading)
            {
                var updateOnNextChange = _.bind(function ()
                {
                    if (this.searchParameters.get('sortBy') !== this.getHeadingSearchField(heading))
                        heading.children('.search-caret').removeClass('caret caret-reversed');

                    // Unbind the callback from whichever event hasn't just been triggered
                    this.searchParameters.off('change:sortBy change:reverseSort', updateOnNextChange);
                }, this);

                this.searchParameters.once('change:sortBy change:reverseSort', updateOnNextChange);
            },

            serializeData: function()
            {
                return {
                    query: this.searchParameters.get('query'),
                    searchType: this.searchParameters.get('field'),
                    numFound: this.collection.metadata ? this.collection.metadata.numFound : 0,
                    showManuscriptName: this.showManuscriptName
                };
            }
        });
    });
