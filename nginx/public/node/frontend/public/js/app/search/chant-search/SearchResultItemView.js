import _ from 'underscore';
import Radio from 'backbone.radio';
import Marionette from 'marionette';
import { Collapse } from 'bootstrap';

import template from './search-result-item.template.html';


var manuscriptChannel = Radio.channel('manuscript');

/**
 * View representing a single search result
 */
export default Marionette.View.extend({
    template,

    // Each result view gets its own tbody element.
    // Note that having more than one tbody per table is perfectly legal:
    // see permitted content in
    // <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>
    tagName: 'tbody',

    ui: {
        chantLink: '.chant-link',
        quickView: '.quick-view',
        fullRecord: '.full-result-record',
    },

    events: {
        'click @ui.quickView': '_onQuickViewClicked',
        'click @ui.chantLink': '_onChantLinkClicked'
    },

    _onQuickViewClicked: function (evt) {
        evt.preventDefault();

        this.ui.fullRecord.toggle();
    },

    _onChantLinkClicked: function () {
        manuscriptChannel.request('set:imageURI', this.model.get('image_uri'), { replaceState: true });
    },

    _getFields: function () {
        return _.toArray(this.getOption('infoFields'));
    },

    onRender: function () {
        this.ui.quickView.tooltip();
        new Collapse(this.ui.fullRecord, { toggle: false });
    },

    serializeData: function () {
        var searchType = this.getOption('searchType');
        var query = this.getOption('query');
        var infoFields = this._getFields();

        return {
            infoFields: infoFields,
            showManuscript: this.getOption('showManuscript'),
            searchType: searchType,
            result: this.model.getFormattedData(searchType, query),
            isVolpianoSearch: searchType === 'volpiano' || searchType === 'volpiano_literal',
            columnCount: infoFields.length + 2
        };
    }
});
