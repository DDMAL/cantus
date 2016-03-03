import Marionette from "marionette";
import ManuscriptItemBaseView from "views/ManuscriptItemBaseView";
import futureManuscripts from "views/futureManuscripts";

export default Marionette.CollectionView.extend({
    tagName: 'tbody',
    childView: ManuscriptItemBaseView,
    collection: futureManuscripts
});
