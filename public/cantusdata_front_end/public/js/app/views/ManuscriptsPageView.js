define( ['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "views/AlertView",
        "views/ManuscriptCollectionView",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
    function(App, Backbone, Marionette, $,
             CantusAbstractView,
             AlertView,
             ManuscriptCollectionView,
             GlobalEventHandler,
             GlobalVars,
             template) {

        "use strict";

        /**
         * This page is a big list of manuscripts.
         *
         * @type {*|void}
         */
        return CantusAbstractView.extend
        ({
            el: '#view-goes-here',

            loaded: false,

            //Subviews
            manuscriptCollectionView: null,
            loadingAlertView: null,

            initialize: function()
            {
                _.bindAll(this, "render", "update", "afterFetch");
                this.template= _.template($('#manuscripts-page-template').html());
                //Subviews
                this.manuscriptCollectionView = new ManuscriptCollectionView(
                    {url: GlobalVars.siteUrl + "manuscripts/"});
                this.loadingAlertView = new AlertView({content:"Loading manuscripts...", role:"info"});
                // Listen for changes
                this.listenTo(this.manuscriptCollectionView.collection, 'sync', this.afterFetch);
            },

            update: function()
            {
                this.manuscriptCollectionView.update();
            },

            afterFetch: function()
            {
                // The manuscripts are loaded, so we don't need the loading bar...
                this.loaded = true;
                this.render();
            },

            render: function()
            {
                console.log("Rendering ManuscriptsPageView");
                console.log(this.$el);
                console.log(this.template());
                $(this.el).html(this.template());
                if (this.loaded)
                {
                    this.assign(this.manuscriptCollectionView, '.manuscript-list');
                }
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });