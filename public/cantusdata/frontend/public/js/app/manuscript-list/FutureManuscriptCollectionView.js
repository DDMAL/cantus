import Marionette from "marionette";
import ManuscriptItemBaseView from "./ManuscriptItemBaseView";
import futureManuscripts from "./futureManuscripts";

export default Marionette.CollectionView.extend({
    tagName: 'tbody',
    childView: ManuscriptItemBaseView,
    collection: futureManuscripts
});
