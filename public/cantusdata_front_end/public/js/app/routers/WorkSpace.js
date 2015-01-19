define(["jquery", "backbone",
        "models/GlobalStateModel",
        "views/HeaderView",
        "views/IndexPageView",
        "views/ManuscriptsPageView",
        "views/BrowserResizer",
        "views/ManuscriptIndividualPageView",
        "views/SearchPageView",
        "singletons/GlobalEventHandler"],
    function($, Backbone,
             GlobalStateModel,
             HeaderView,
             IndexPageView,
             ManuscriptsPageView,
             BrowserResizer,
             ManuscriptIndividualPageView,
             SearchPageView,
             GlobalEventHandler) {

        "use strict";

        return Backbone.Router.extend
        ({
            // The global state model
            globalState: null,
            // Common to all routes
            headerView: null,
            // Only on certain routes
            indexView: null,
            manuscriptsPageView: null,
            manuscriptView: null,
            searchPageView: null,
            // Browser resizer
            resizer: null,

            routes: {
                "" : "manuscripts",
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
                // There is always a header!
                this.headerView = new HeaderView({el:".header"});
                this.headerView.render();

                // IndexPageView has no state, so we might as well instantiate it
                this.indexView = new IndexPageView();
                // Same with manuscripts page
                this.manuscriptsPageView = new ManuscriptsPageView();
                // Get the resizer going
                this.resizer = new BrowserResizer();
            },

            index: function()
            {
                console.log("index route");
                this.indexView.render();
            },

            manuscripts: function()
            {
                console.log("manuscripts route");
                this.manuscriptsPageView.update();
                this.manuscriptsPageView.render();
            },

            manuscriptSingle: function(query, folio, chant)
            {
                console.log("manuscript single route. query:", query, "folio:", folio, "chant:", chant);
                if (this.manuscriptView !== null)
                {
                    // We want to make sure that the old view, if it exists, is
                    // completely cleared-out.
                    this.manuscriptView.divaView.uninitializeDiva();
                    //this.manuscriptView.remove();
                    this.manuscriptView.destroy();
                    this.manuscriptView = null;
                }

                this.manuscriptView = new ManuscriptIndividualPageView(
                    {
                        id: query,
                        folio: folio
                    }
                );
                //console.log(this.manuscriptView);
                // Fetch the data
                this.manuscriptView.getData();
                //this.manuscriptView.render();

                GlobalEventHandler.trigger("ChangeManuscript", query);
                GlobalEventHandler.trigger("ChangeChant", chant);
            },

            search: function(query)
            {
                console.log("search view");
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