define(["backbone",
        "marionette",
        "models/GlobalStateModel",
        "views/HeaderView",
        "views/ManuscriptsPageView",
        "views/BrowserResizer",
        "views/ManuscriptIndividualPageView",
        "views/SearchPageView",
        "singletons/GlobalEventHandler"],
function(Backbone,
         Marionette,
         GlobalStateModel,
         HeaderView,
         ManuscriptsPageView,
         BrowserResizer,
         ManuscriptIndividualPageView,
         SearchPageView,
         GlobalEventHandler)
{

"use strict";

return Backbone.Router.extend
({
    // The global state model
    globalState: null,
    // Common to all routes
    headerView: null,
    // Only on certain routes
    manuscriptsPageView: null,
    manuscriptView: null,
    searchPageView: null,
    // Browser resizer
    resizer: null,

    headerRegion: null,
    mainBodyRegion: null,

    routes: {
        "": "manuscripts",
        "manuscript/:query/?folio=(:folio)&chant=(:chant)": "manuscriptSingle",
        "manuscript/:query/?folio=(:folio)": "manuscriptSingle",
        "manuscript/:query/": "manuscriptSingle",
        "manuscripts/": "manuscripts",
        "search/?q=(:query)": "search",
        "search/": "search",
        '*path': "notFound"
    },

    // We always want the header
    initialize: function()
    {
        this.globalState = new GlobalStateModel();

        // Regions
        // There is always a header!
        this.headerView = new HeaderView({el: ".header"});
        this.headerView.render();

        //this.headerRegion = new Marionette.Region({el: '.header'});
        this.mainBodyRegion = new Marionette.Region({
            el: document.querySelector("#view-goes-here")
        });
        //
        //this.headerRegion.show(new HeaderView());

        // The manuscripts page has no state, so we might as well instantiate it
        this.manuscriptsPageView = new ManuscriptsPageView();
        // Get the resizer going
        this.resizer = new BrowserResizer();
    },

    manuscripts: function()
    {
        //var view = new ManuscriptsPageView();
        //view.update();
        if (this.manuscriptView !== null)
        {
            this.manuscriptView.destroy();
        }
        this.manuscriptView = null;
        this.manuscriptsPageView.render();

        // Set the document title to reflect the manuscripts route
        GlobalEventHandler.trigger("ChangeDocumentTitle", "Manuscripts");
    },

    manuscriptSingle: function(query, folio, chant)
    {
        if (this.manuscriptView !== null)
        {
            // We want to make sure that the old view, if it exists, is completely cleared-out.
            this.manuscriptView.destroy();
            this.manuscriptView = null;
        }

        this.manuscriptView = new ManuscriptIndividualPageView(
            {
                id: query,
                folio: folio
            }
        );
        // Fetch the data
        this.manuscriptView.getData();
        //this.manuscriptView.render();

        GlobalEventHandler.trigger("ChangeManuscript", query);
        GlobalEventHandler.trigger("ChangeFolio", folio);
        GlobalEventHandler.trigger("ChangeChant", chant);
    },

    search: function(query)
    {
        // Delete a search view if it exists
        if (this.searchView !== null && this.searchView !== undefined)
        {
            this.searchView.remove();
            this.searchView = null;
        }

        this.searchView = new SearchPageView({query: query});
        this.searchView.render();
    },

    notFound: function()
    {
        // TODO: Handle 404 somehow
    }
});
});