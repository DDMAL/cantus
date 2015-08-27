define(['underscore', 'jquery', 'marionette', 'views/item_views/SearchResultItemView', 'utils/lastChildVisible'],
    function(_, $, Marionette, SearchResultItemView, lastChildVisible)
    {

        "use strict";

        // TODO(wabain): this is misnamed since it's actually a CompositeView

        /**
         * Determine whether an element has been hidden by having
         * display: none set.
         *
         * @param jqElem
         * @returns {boolean}
         * @private
         */
        function isDisplayed(jqElem)
        {
            return jqElem.css('display') !== 'none';
        }

        /**
         * View representing a Search Result with count.
         */
        return Marionette.CompositeView.extend({
            template: "#search-result-list-template",

            childView: SearchResultItemView,
            childViewContainer: '.child-container',

            reorderOnSort: true,

            collectionEvents: {
                "update reset": "hideIfEmpty"
            },

            behaviors: {
                resize: {
                    target: '.result-table-wrapper',
                    allowSmaller: true
                }
            },

            ui: {
                resultList: '.result-list',
                resultListWrapper: '.result-table-wrapper',
                resultHeading: '.result-list th'
            },

            events: {
                'click @ui.resultHeading': 'changeSortCriterion'
            },

            initialize: function()
            {
                // FIXME(wabain): update this to use mergeOptions after updating Marionette
                this.searchParameters = this.getOption('searchParameters');

                this._handleScroll = _.throttle(_.bind(this._loadResultsIfAtEnd, this), 250);

                this.listenTo(this.searchParameters, 'change:sortBy change:reverseSort', this._triggerSortingChanged);
                this.listenTo(this.searchParameters, 'change:query change:field', this._resetScrolling);
            },

            childViewOptions: function ()
            {
                return {
                    searchType: this.searchParameters.get('field'),
                    query: this.searchParameters.get('query'),
                    infoFields: this.getOption('infoFields')
                };
            },

            onRenderTemplate: function ()
            {
                this.hideIfEmpty();
                this.triggerMethod('sorting:changed');
                this.triggerMethod('recalculate:size');

                // We can't use the events hash for this because it relies on events
                // bubbling, and the scroll event does not bubble
                this.ui.resultListWrapper.on('scroll', this._handleScroll);
            },

            _triggerSortingChanged: function ()
            {
                this.triggerMethod('sorting:changed');
            },

            _resetScrolling: function ()
            {
                if (this.isRendered)
                    this.ui.resultListWrapper.scrollTop(0);
            },

            /**
             * If there is no query then hide the view. If there is a
             * query but no results then hide the result table.
             */
            hideIfEmpty: function ()
            {
                if (!this.searchParameters.get('query'))
                {
                    this.$el.hide();
                    return;
                }

                // We need to trigger a sizing recalculation if either
                // the view's root element or the result list is shown
                var requiresSizeCalculation;

                if (isDisplayed(this.$el))
                {
                    requiresSizeCalculation = false;
                }
                else
                {
                    requiresSizeCalculation = true;
                    this.$el.show();
                }

                if (this.collection.length === 0)
                {
                    this.ui.resultList.hide();
                }
                else if (!isDisplayed(this.ui.resultList))
                {
                    requiresSizeCalculation = true;
                    this.ui.resultList.show();
                }

                if (requiresSizeCalculation)
                    this.triggerMethod('recalculate:size');
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

            onSortingChanged: function ()
            {
                // Set the caret on the result table heading which corresponds
                // to the field which is being sorted by
                var sortField = this.searchParameters.get('sortBy');

                _.some(this.ui.resultHeading, function (heading)
                {
                    heading = $(heading);

                    if (this.getHeadingSearchField(heading) === sortField)
                    {
                        this._setHeadingCaret(heading);
                        return true;
                    }
                }, this);
            },

            /**
             * Update the caret representing the sort ordering on the result table heading which
             * corresponds to the field which is being sorted by.
             *
             * @param heading The heading for the active row
             * @private
             */
            _setHeadingCaret: function (heading)
            {
                heading.children('.search-caret')
                    .addClass('caret')
                    .toggleClass('caret-reversed', this.searchParameters.get('reverseSort'));

                // Register a callback to clear the state of the heading the next time that
                // the sort criteria change. We need to defer this because otherwise it could be triggered
                // immediately if we're in the middle of dispatching sorting:changed callbacks
                _.defer(_.bind(this.once, this), 'sorting:changed', function ()
                {
                    if (this.searchParameters.get('sortBy') !== this.getHeadingSearchField(heading))
                        heading.children('.search-caret').removeClass('caret caret-reversed');
                });
            },

            /**
             * If the last item in the results list is scrolled into view, then request more items
             * @private
             */
            _loadResultsIfAtEnd: function ()
            {
                // If the last child element is visible, request more items. This is a
                // pretty noisy trigger, but the incremental load handler ignores
                // duplicate requests, and it's better to to be overly broad in
                // defining the condition for loading rather than insufficiently so.
                if (lastChildVisible(this, this.ui.resultListWrapper))
                    this.trigger('continue:loading');
            },

            templateHelpers: function()
            {
                return {
                    infoFields: _.toArray(this.getOption('infoFields'))
                };
            }
        });
    });
