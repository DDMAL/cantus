import Marionette from "marionette";

import GlobalVars from "config/GlobalVars";
import ManuscriptCollection from "collections/ManuscriptCollection";

import ManuscriptCollectionView from "./ManuscriptCollectionView";

import template from './manuscript-list-page.template.html';

/**
 * This page is a big list of manuscripts.
 */
export default Marionette.LayoutView.extend({
    template,

    regions: {
        manuscriptList: '.manuscript-list',
    },

    onRender: function ()
    {
        var collection = new ManuscriptCollection();
        collection.fetch({url: GlobalVars.siteUrl + "manuscripts/"});

        // We attach the view to the region element because
        // we need direct child relationships for the table
        var availableManuscripts = new ManuscriptCollectionView({
            collection: collection,
            el: this.$(this.manuscriptList.el)
        });

        availableManuscripts.render();
        this.manuscriptList.attachView(availableManuscripts);
    }
});
