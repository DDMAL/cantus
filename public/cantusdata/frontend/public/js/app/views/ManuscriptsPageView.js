define(["marionette",
        "collections/ManuscriptCollection",
        "views/ManuscriptCollectionView",
        "config/GlobalVars"],
    function(Marionette,
             ManuscriptCollection,
             ManuscriptCollectionView,
             GlobalVars)
    {

        "use strict";

        /**
         * This page is a big list of manuscripts.
         */
        return Marionette.LayoutView.extend({
            template: '#manuscripts-page-template',

            regions: {
                manuscriptList: '.manuscript-list'
            },

            onRender: function ()
            {
                var collection = new ManuscriptCollection();
                collection.fetch({url: GlobalVars.siteUrl + "manuscripts/"});

                this.manuscriptList.show(new ManuscriptCollectionView({
                    collection: collection
                }));
            }
        });
    });