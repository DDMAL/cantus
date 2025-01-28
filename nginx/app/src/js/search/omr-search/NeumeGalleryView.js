import _ from 'underscore';
import Marionette from 'marionette';
import pageSnippetUrl from 'utils/pageSnippetUrl';

import template from './neume-gallery-list.template.html';
import childTemplate from './neume-gallery-item.template.html';

export default Marionette.CollectionView.extend({
    template,

    onChildviewExemplarClicked: function (view) {
        this.trigger('use:neume', view.model.get('name'));
    },

    childViewContainer: '.child-container',

    childView: Marionette.View.extend({
        template: childTemplate,

        triggers: {
            'click .neume-gallery-entry': 'exemplar:clicked'
        },

        templateContext: {
            exemplarUrl: function () {
                // jscs:disable requireCamelCaseOrUpperCaseIdentifiers
                return pageSnippetUrl(_.pick(this, ['p', 'x', 'y', 'w', 'h']), { height: 50 });
                // jscs enable
            }
        }
    })
});
