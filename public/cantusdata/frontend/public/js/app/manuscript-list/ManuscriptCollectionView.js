import Marionette from "marionette";
import ManuscriptItemView from "./ManuscriptItemView";

import emptyTemplate from './manuscript-collection-empty.template.html';

export default Marionette.CollectionView.extend({
    tagName: 'tbody',

    childView: ManuscriptItemView,
    emptyView: Marionette.ItemView.extend({
        tagName: 'tr',
        template: emptyTemplate
    })
});
