define(["marionette",
        "views/ManuscriptCollectionView",
        "config/GlobalVars"],
    function(Marionette,
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
                this.manuscriptList.show(new ManuscriptCollectionView({
                    url: GlobalVars.siteUrl + "manuscripts/"
                }));
            }
        });
    });