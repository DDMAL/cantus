define(["marionette",
        "collections/ManuscriptCollection",
        "views/ManuscriptCollectionView",
        "views/FutureManuscriptCollectionView",
        "config/GlobalVars"],
    function(Marionette,
             ManuscriptCollection,
             ManuscriptCollectionView,
             FutureManuscriptCollectionView,
             GlobalVars)
    {

        "use strict";

        /**
         * This page is a big list of manuscripts.
         */
        return Marionette.LayoutView.extend({
            template: '#manuscripts-page-template',

            regions: {
                manuscriptList: '.manuscript-list',
                futureManuscriptList: '.future-manuscript-list'
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

                var futureManuscripts = new FutureManuscriptCollectionView({
                    el: this.$(this.futureManuscriptList.el)
                });

                futureManuscripts.render();
                this.futureManuscriptList.attachView(futureManuscripts);
            }
        });
    });