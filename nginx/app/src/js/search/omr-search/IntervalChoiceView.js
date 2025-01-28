import Marionette from 'marionette';

import template from './interval-choice-list.template.html';

export default Marionette.CollectionView.extend({
    template,

    events: {
        'click [data-search-value]': 'onChoiceClicked'
    },

    onChoiceClicked: function (event) {
        this.trigger('use:interval', $(event.target).attr('data-search-value'));
    }
});