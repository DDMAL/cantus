define( ['App', 'backbone', 'marionette', 'jquery',
        "models/Folio",
        "views/CantusAbstractView",
        "views/collection_views/ChantCompositeView",
        "views/item_views/FolioItemView",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
function(App, Backbone, Marionette, $,
         Folio,
         CantusAbstractView,
         ChantCompositeView,
         FolioItemView,
         GlobalEventHandler,
         GlobalVars)
{

"use strict";

/**
 * Provide an alert message to the user.
 */
return Marionette.LayoutView.extend
({
    /**
     * customNumber is the folio number that we actually render.
     */
    customNumber: 0,

    // Subviews
    chantCompositeView: null,
    folioItemView: null,

    template: "#folio-template",

    regions: {
        chantListRegion: '.chant-list-region',
        folioItemRegion: '.folio-item-region'
    },

    /**
     *
     *
     * @param {type} options
     * @returns null
     */
    initialize: function(options)
    {
        _.bindAll(this, 'afterFetch', 'assignChants');
        // This can handle situations where the first folio
        // doesn't have a url but subsequent ones do.

        this.model = new Folio();
        this.listenTo(this.model, 'sync', this.afterFetch);

        if (options && options.url)
        {
            this.setUrl(options.url);
        }
        this.folioItemView = new FolioItemView({
            model: this.model
        });
        this.chantCompositeView = new ChantCompositeView({
            collection: new Backbone.Collection()
        });
    },

    onDestroy: function()
    {
        this.chantCompositeView.destroy();
        this.folioItemView.destroy();
    },

    /**
     * Set the model URL.
     *
     * @param url
     */
    setUrl: function(url)
    {
        this.model.url = String(url);
        this.model.fetch();
    },

    /**
     * Set the parameter that overrides the number that's rendered to the
     * screen.
     *
     * @param number
     */
    setCustomNumber: function(number)
    {
        this.customNumber = number;
        this.model.set({number: number, item_id: undefined});
    },

    /**
     * If the model is empty, un-render the view.  Otherwise, assign
     * the chants and render the view.
     */
    afterFetch: function()
    {
        this.assignChants();
        this.chantListRegion.show(this.chantCompositeView);
    },

    /**
     * Rebuild the list of chants
     */
    assignChants: function()
    {
        // We are going to query this data from SOLR because it's faster.
        // So we need the manuscript siglum and folio name.
        // We need to handle the data differently depending on whether
        // we're getting the information from Django or Solr.
        var folio_id;
        if (this.model.get("item_id"))
        {
            folio_id = this.model.get("item_id");
            // Compose the url
            var composedUrl = GlobalVars.siteUrl + "chant-set/folio/" + folio_id + "/";
            // Build a new view with the new data
            this.chantCompositeView.setUrl(composedUrl);
        }
        else
        {
            this.chantCompositeView.resetCollection();
        }
    },

    onShow: function()
    {
        //// Show the chant list without destroying the original
        ////this.chantListRegion.show(this.chantCompositeView);
        this.folioItemRegion.show(this.folioItemView);
        GlobalEventHandler.trigger("renderView");
    }
});
});