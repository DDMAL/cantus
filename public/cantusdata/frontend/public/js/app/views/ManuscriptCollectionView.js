import Marionette from "marionette";
import ManuscriptItemView from "views/ManuscriptItemView";

export default Marionette.CollectionView.extend({
    tagName: 'tbody',

    childView: ManuscriptItemView,
    emptyView: Marionette.ItemView.extend({
        tagName: 'tr',
        template: '#manuscript-collection-empty-template'
    })
});
