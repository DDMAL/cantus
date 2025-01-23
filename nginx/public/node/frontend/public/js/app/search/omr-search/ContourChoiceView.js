import Marionette from 'marionette';
import $ from 'jquery';

import template from './contour-choice-list.template.html';

export default Marionette.CollectionView.extend({
    template,

    events: {
        'click [data-search-value]': 'onChoiceClicked'
    },

    onChoiceClicked: function (event) {
        this.trigger('use:contour', $(event.target).attr('data-search-value'));
    }
});