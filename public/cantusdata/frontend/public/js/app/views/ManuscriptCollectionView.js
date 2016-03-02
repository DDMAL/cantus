define(["marionette",
        "views/ManuscriptItemView"],
    function(Marionette,
             ManuscriptItemView)
    {

        "use strict";

        return Marionette.CollectionView.extend({
            tagName: 'tbody',

            childView: ManuscriptItemView,
            emptyView: Marionette.ItemView.extend({
                tagName: 'tr',
                template: '#manuscript-collection-empty-template'
            })
        });
    });