define(["marionette", "views/ManuscriptItemBaseView", "views/futureManuscripts"],
function(Marionette, ManuscriptItemBaseView, futureManuscripts)
{
    'use strict';

    return Marionette.CollectionView.extend({
        tagName: 'tbody',
        childView: ManuscriptItemBaseView,
        collection: futureManuscripts
    });
});
