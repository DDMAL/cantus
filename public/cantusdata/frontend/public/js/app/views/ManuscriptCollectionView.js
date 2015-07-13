define(["marionette",
        "collections/ManuscriptCollection",
        "views/ManuscriptItemView"],
    function(Marionette,
             ManuscriptCollection,
             ManuscriptItemView)
    {

        "use strict";

        return Marionette.CollectionView.extend({
            tagName: 'ul',

            childView: ManuscriptItemView,

            // This view gets rendered in an <ul> despite not being a <li>,
            // which is inelegant at best, but temporary
            emptyView: Marionette.ItemView.extend({
                template: '#manuscript-collection-empty-template'
            }),

            initialize: function(options)
            {
                this.collection = new ManuscriptCollection();
                this.collection.fetch({url: options.url});
            }
        });
    });