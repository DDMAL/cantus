define(['marionette',
        "models/Manuscript",
        "views/FolioView",
        "views/DivaView",
        "views/InternalSearchView",
        "views/SearchNotationView",
        "views/ManuscriptDataPopoverView",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
function(Marionette,
         Manuscript,
         FolioView,
         DivaView,
         InternalSearchView,
         SearchNotationView,
         ManuscriptDataPopoverView,
         GlobalEventHandler,
         GlobalVars)
{

"use strict";

/**
 * This page shows an individual manuscript.  You get a nice diva viewer
 * and you can look through the chant info.
 *
 * @type {*|void}
 */
return Marionette.LayoutView.extend
({
    el: '#view-goes-here',
    template: '#manuscript-template',

    id: null,
    manuscript: null,
    searchView: null,
    searchNotationView: null,
    popoverContent: null,

    // Subviews
    divaView: null,
    folioView: null,

    ui: {
        manuscriptTitleContainer: '#manuscript-title-container',
        manuscriptTitlePopoverLink: '#manuscript-title-popover-link'
    },

    // FIXME(wabain): use inserted.bs.popover after updating bootstrap
    events: {
        'shown.bs.popover @ui.manuscriptTitlePopoverLink': 'instantiatePopoverView',
        'hidden.bs.popover @ui.manuscriptTitlePopoverLink': 'destroyPopoverView'
    },

    regions: {
        divaViewRegion: "#diva-column",
        folioViewRegion: "#folio",
        searchViewRegion: "#manuscript-search",
        searchNotationViewRegion: "#search-notation"
    },

    initialize: function (options)
    {
        _.bindAll(this, 'getPopoverContent');

        this.manuscript = new Manuscript(
            String(GlobalVars.siteUrl + "manuscript/" + this.id.toString() + "/"));
        // Build the subviews
        this.divaView = new DivaView(
            {
                siglum: this.manuscript.get("siglum_slug"),
                folio: options.folio
            }
        );
        this.folioView = new FolioView();
        this.searchView = new InternalSearchView();
        this.searchNotationView = new SearchNotationView(
            {
                divaView: this.divaView
            }
        );

        // Render every time the model changes...
        this.listenTo(this.manuscript, 'change', this.afterFetch);
        // Switch page when necessary
        this.listenTo(GlobalEventHandler, "ChangeFolio", this.updateFolio);
    },

    remove: function()
    {
        // Deal with the event listeners
        this.stopListening();
        this.undelegateEvents();
        // Nullify the manuscript model
        this.manuscript = null;
        // Nullify the views
        this.divaView = null;
        this.searchView = null;
        this.searchNotationView = null;
        this.folioView = null;
        // Remove from the dom
        this.$el.empty();
    },

    /**
     * Marionette method called automatically before the destroy event happens.
     */
    onBeforeDestroy: function()
    {
        this.divaView.destroy();
        this.searchView.destroy();
        this.searchNotationView.destroy();
        this.folioView.destroy();
        this.destroyPopoverView();
    },

    instantiatePopoverView: function ()
    {
        this.popoverView = new ManuscriptDataPopoverView({
            el: this.ui.manuscriptTitleContainer.find('.popover')
        });
    },

    destroyPopoverView: function ()
    {
        if (this.popoverView)
        {
            this.popoverView.destroy();
            this.popoverView = null;
        }
    },

    /**
     * Update the view for a changed folio
     */
    updateFolio: function(folio)
    {
        // FIXME(wabain): this is a patch to get an ID reliably
        // but the underlying issue here is the unclear division of responsibility
        // between models and views
        var id = this.manuscript.get('id');
        if (id === void 0)
            id = this.id;

        // Query the folio set at that specific manuscript number
        var newUrl =  GlobalVars.siteUrl + "folio-set/manuscript/" + id + "/" + folio + "/";

        // Rebuild the folio View
        this.folioView.setCustomNumber(folio);
        this.folioView.setUrl(newUrl);
    },

    /**
     * Fetch the manuscript's data from the API.
     */
    getData: function()
    {
        this.manuscript.fetch();
    },

    /**
     * Get the HTML content for the manuscript data popover, generating it from a template if it has not
     * already been initialized.
     *
     * @returns {string}
     */
    getPopoverContent: function ()
    {
        if (!this.popoverContent)
            this.popoverContent = Marionette.TemplateCache.get('#manuscript-data-template')(this.serializeData());

        return this.popoverContent;
    },

    afterFetch: function()
    {
        // Figure out what search fields to activate
        var notationSearchFields = {};

        if (this.manuscript.isPluginActivated("pitch-search"))
        {
            notationSearchFields.pnames = "Pitch";
        }
        if (this.manuscript.isPluginActivated("neume-search"))
        {
            notationSearchFields.neumes = "Neume";
        }

        // Set the search view to only search this manuscript
        this.searchView.setRestriction('manuscript', '"' + this.manuscript.get("siglum") + '"');
        this.divaView.setManuscript(this.manuscript.get("siglum_slug"));
        this.searchNotationView.setManuscript(this.manuscript.get("siglum_slug"));
        this.searchNotationView.setSearchFields(notationSearchFields);
        this.render();

        // Set the document title to reflect the manuscript name
        GlobalEventHandler.trigger("ChangeDocumentTitle", this.manuscript.get("name"));
    },

    /**
     * Serialize the manuscript before rendering the template.
     *
     * @returns {*}
     */
    serializeData: function()
    {
        return this.manuscript.toJSON();
    },

    onRender: function()
    {
        this.ui.manuscriptTitlePopoverLink.popover({
            content: this.getPopoverContent,
            html: true
        });

        // Render subviews
        if (this.divaView !== undefined)
        {
            this.divaViewRegion.show(this.divaView, {preventDestroy: true});
            this.folioViewRegion.show(this.folioView, {preventDestroy: true});
        }

        this.searchViewRegion.show(this.searchView);
        this.searchNotationViewRegion.show(this.searchNotationView);
        GlobalEventHandler.trigger("renderView");
    }
});
});
