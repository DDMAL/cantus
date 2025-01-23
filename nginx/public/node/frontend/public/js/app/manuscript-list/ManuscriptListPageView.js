import Marionette from "marionette";


import ManuscriptItemView from "./ManuscriptItemView";

import template from './manuscript-list-page.template.html';

/**
 * This page is a list of manuscripts.
 */
export default Marionette.CollectionView.extend({
    template,
    childViewContainer: '.manuscript-list',
    childView: ManuscriptItemView,
});
