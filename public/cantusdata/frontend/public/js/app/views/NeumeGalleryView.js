define(['underscore', 'marionette'], function (_, Marionette)
{
    "use strict";

    return Marionette.CompositeView.extend({
        template: '#neume-gallery-list-template',

        onChildviewExemplarClicked: function (view)
        {
            this.trigger('use:neume', view.model.get('neume'));
        },

        childViewContainer: '.child-container',

        childView: Marionette.ItemView.extend({
            template: '#neume-gallery-item-template',

            triggers: {
                'click .thumbnail': 'exemplar:clicked'
            }
        })
    });
});