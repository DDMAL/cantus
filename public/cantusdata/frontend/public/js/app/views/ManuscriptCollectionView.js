define(["marionette",
        "views/ManuscriptItemView"],
    function(Marionette,
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
            })
        });
    });