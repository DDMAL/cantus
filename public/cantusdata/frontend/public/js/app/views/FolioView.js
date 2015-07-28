define(['underscore', 'backbone', 'marionette',
        "models/Folio",
        "collections/ChantCollection",
        "views/collection_views/ChantCompositeView",
        "views/DivaFolioAdvancerView",
        "views/item_views/FolioItemView",
        "config/GlobalVars"],
function(_, Backbone, Marionette,
         Folio,
         ChantCollection,
         ChantCompositeView,
         DivaFolioAdvancerView,
         FolioItemView,
         GlobalVars)
{

"use strict";

var manuscriptChannel = Backbone.Radio.channel('manuscript');

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
    initialize: function()
    {
        if (!this.model)
        {
            this.model = new Folio();
            this.updateFolio();
        }

        this.chantCollection = new ChantCollection();

        this.listenTo(this.model, 'sync', this.afterFetch);
        this.listenTo(manuscriptChannel, 'change:folio', this.updateFolio);
    },

    updateFolio: function ()
    {
        //this.model.clear();

        var manuscript = manuscriptChannel.request('manuscript');
        var folioNumber = manuscriptChannel.request('folio');

        // jshint eqnull:true
        if (folioNumber == null || manuscript == null)
        {
            return;
        }

        this.model.fetch({
            url: GlobalVars.siteUrl + "folio-set/manuscript/" + manuscript + "/" + folioNumber + "/"
        });
    },

    afterFetch: function ()
    {
        this.assignChants();

        if (this.folioItemRegion.currentView)
            this.folioItemRegion.currentView.render();
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
        this.folioItemRegion.show(new FolioItemView({model: this.model}));

        this.chantListRegion.show(new ChantCompositeView({
            collection: this.chantCollection,
            unfoldedChant: manuscriptChannel.request('chant')
        }));

        this.divaFolioAdvancerRegion.show(new DivaFolioAdvancerView());
    }
});
});