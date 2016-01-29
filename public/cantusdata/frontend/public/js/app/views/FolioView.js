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

return Marionette.LayoutView.extend({
    template: "#folio-template",

    regions: {
        chantListRegion: '.chant-list-region',
        folioItemRegion: '.folio-item-region',
        divaFolioAdvancerRegion: '.diva-folio-advancer-region'
    },

    modelEvents: {
        sync: '_onFetch',
        error: '_handleFetchError'
    },

    initialize: function()
    {
        this.chantCollection = new ChantCollection();

        if (!this.model)
        {
            this.model = new Folio();
            this.updateFolio();
        }

        this.listenTo(manuscriptChannel, 'change:folio', this.updateFolio);
    },

    updateFolio: function ()
    {
        var manuscript = manuscriptChannel.request('manuscript');
        var folioNumber = manuscriptChannel.request('folio');

        // jshint eqnull:true
        if (folioNumber == null || manuscript == null)
        {
            return;
        }

        var loaded = false;

        // Display a loading message if the chants don't load almost immediately
        _.delay(_.bind(function ()
        {
            if (!loaded)
            {
                this.chantCollection.reset();
                this._showMessage('Loading...');
            }
        }, this), 250);

        this.model.fetch({
            url: GlobalVars.siteUrl + "folio-set/manuscript/" + manuscript + "/" + folioNumber + "/"
        }).always(function ()
        {
            loaded = true;
        });
    },

    _onFetch: function ()
    {
        this.assignChants();
    },

    _handleFetchError: function (model, xhr)
    {
        this.chantCollection.reset();
        this.model.clear();

        // We can ignore 404s and take them to mean no data
        if (xhr.status === 404)
            this.assignChants();
        else
            this._showMessage('Failed to load chants.');
    },

    /** Display a message */
    _showMessage: function (message)
    {
        // FIXME: This is a pretty fragile way to display a message.
        // Really this should probably all be in templates.
        if (this.chantListRegion.currentView)
        {
            if (message)
                this.chantListRegion.currentView.ui.errorMessages.text(message);
            else
                this.chantListRegion.currentView.ui.errorMessages.empty();
        }
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

            // Clear a loading message if one is displayed
            this._showMessage(null);
        }
        else
        {
            this.chantCollection.reset();
        }
    },

    onShow: function()
    {
        this.folioItemRegion.show(new FolioItemView());

        this.chantListRegion.show(new ChantCompositeView({
            collection: this.chantCollection,
            unfoldedChant: manuscriptChannel.request('chant')
        }));

        this.divaFolioAdvancerRegion.show(new DivaFolioAdvancerView());
    }
});
});
