define(['underscore', 'backbone', 'marionette',
        "models/Folio",
        "collections/ChantCollection",
        "views/collection_views/ChantCompositeView",
        "views/DivaFolioAdvancerView",
        "views/item_views/FolioItemView",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
function(_, Backbone, Marionette,
         Folio,
         ChantCollection,
         ChantCompositeView,
         DivaFolioAdvancerView,
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
        folioItemRegion: '.folio-item-region',
        divaFolioAdvancerRegion: '.diva-folio-advancer-region'
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
        this.chantCollection = new ChantCollection();

        this.listenTo(this.model, 'sync', this.afterFetch);

        if (options && options.url)
        {
            this.setUrl(options.url);
        }

        this.folioItemView = new FolioItemView({
            model: this.model
        });

        this.chantCompositeView = new ChantCompositeView({
            collection: this.chantCollection,
            unfoldedChant: this.getActiveChant()
        });
    },

    /**
     * Return the current active chant for the application
     */
    getActiveChant: function()
    {
        // FIXME(wabain): requiring the app in a closure resolves a circular import issue, but it's
        // a little iffy in terms of bundler tooling and goes against the general CU code style. This
        // should probably use a channel or something.
        return require('App').routeController.globalState.get('chant');
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
        this.model.set({number: number, 'item_id': undefined});
    },

    /**
     * If the model is empty, un-render the view.  Otherwise, assign
     * the chants and render the view.
     */
    afterFetch: function()
    {
        this.assignChants();
    },

    /**
     * Rebuild the list of chants
     */
    assignChants: function()
    {
        // TODO(wabain): normalize Solr differences in model.parse methods
        // We are going to query this data from SOLR because it's faster.
        // So we need the manuscript siglum and folio name.
        // We need to handle the data differently depending on whether
        // we're getting the information from Django or Solr.
        if (this.model.get("item_id"))
        {
            // Compose the url
            var composedUrl = GlobalVars.siteUrl + "chant-set/folio/" + this.model.get("item_id") + "/";

            // Update the chant collection
            this.chantCollection.fetch({reset: true, url: composedUrl});
        }
        else
        {
            this.chantCollection.reset();
        }
    },

    onShow: function()
    {
        this.folioItemRegion.show(this.folioItemView, {preventDestroy: true});
        this.chantListRegion.show(this.chantCompositeView, {preventDestroy: true});
        this.divaFolioAdvancerRegion.show(new DivaFolioAdvancerView());
    }
});
});