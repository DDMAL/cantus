define(['underscore', 'jquery', 'marionette', 'utils/afterTransition'],
    function(_, $, Marionette, afterTransition)
    {

        "use strict";

        var FULL_RECORD_TRANSITION_MS = 600;

        function transitionWithClasses(jqElem, ms, baseClass, activeClass)
        {
            var deferred = $.Deferred();

            jqElem.addClass(baseClass);

            jqElem[0].offsetHeight;

            jqElem.addClass(activeClass);

            afterTransition(jqElem, ms, function ()
            {
                jqElem
                    .removeClass(baseClass)
                    .removeClass(activeClass);

                deferred.resolve(jqElem);
            });

            return deferred;
        }

        /**
         * View representing a single search result
         */
        return Marionette.ItemView.extend({
            template: "#search-result-item-template",

            // Each result view gets its own tbody element.
            // Note that having more than one tbody per table is perfectly legal:
            // see permitted content in
            // <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>
            tagName: 'tbody',

            ui: {
                quickView: '.quick-view',
                fullRecord: '.full-result-record',
                fullRecordContent: '.full-result-record-content'
            },

            events: {
                'click @ui.quickView': '_onQuickViewClicked'
            },

            _onQuickViewClicked: function (evt)
            {
                evt.preventDefault();

                if (this.ui.fullRecord.css('display') === 'none')
                    this._showFullRecord();
                else
                    this._hideFullRecord();
            },

            _showFullRecord: function ()
            {
                this.ui.fullRecord.removeClass('hidden');

                transitionWithClasses(
                    this.ui.fullRecordContent,
                    FULL_RECORD_TRANSITION_MS,
                    'content-enter',
                    'content-enter-active'
                );
            },

            _hideFullRecord: function ()
            {
                var fullRecord = this.ui.fullRecord;

                transitionWithClasses(
                    this.ui.fullRecordContent,
                    FULL_RECORD_TRANSITION_MS,
                    'content-exit',
                    'content-exit-active'
                ).then(function ()
                {
                    fullRecord.addClass('hidden');
                });
            },

            _getRecordView: function ()
            {
                return new FullRecordView({
                    colSpan: this._getFields().length + 2,
                    model: this.model
                });
            },

            _getFields: function ()
            {
                return _.toArray(this.getOption('infoFields'));
            },

            onRender: function ()
            {
                this.$('[data-toggle=tooltip]').tooltip();
            },

            serializeData: function()
            {
                var searchType = this.getOption('searchType');
                var query = this.getOption('query');
                var infoFields = this._getFields();

                return {
                    infoFields: infoFields,
                    searchType: searchType,
                    result: this.model.getFormattedData(searchType, query),
                    isVolpianoSearch: searchType === 'volpiano',
                    columnCount: infoFields.length + 2
                };
            }
        });
    });
