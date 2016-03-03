import _ from 'underscore';
import Marionette from 'marionette';
import pageSnippetUrl from 'utils/pageSnippetUrl';

export default Marionette.CompositeView.extend({
    template: '#neume-gallery-list-template',

    onChildviewExemplarClicked: function (view)
    {
        this.trigger('use:neume', view.model.get('name'));
    },

    childViewContainer: '.child-container',

    childView: Marionette.ItemView.extend({
        template: '#neume-gallery-item-template',

        triggers: {
            'click .neume-gallery-entry': 'exemplar:clicked'
        },

        templateHelpers: {
            exemplarUrl: function ()
            {
                // jscs:disable requireCamelCaseOrUpperCaseIdentifiers
                return pageSnippetUrl(this.siglum_slug, _.pick(this, ['p', 'x', 'y', 'w', 'h']), {height: 75});
                // jscs enable
            }
        }
    })
});
