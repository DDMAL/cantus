define(["underscore",
        "backbone",
        "marionette",
        "models/GlobalStateModel",
        "views/RootView",
        "views/HeaderView",
        "views/ManuscriptsPageView",
        "views/BrowserResizer",
        "views/ManuscriptIndividualPageView",
        "views/SearchPageView",
        "singletons/GlobalEventHandler"],
    function(_,
             Backbone,
             Marionette,
             GlobalStateModel,
             RootView,
             HeaderView,
             ManuscriptsPageView,
             BrowserResizer,
             ManuscriptIndividualPageView,
             SearchPageView,
             GlobalEventHandler)
    {
        "use strict";

        return Marionette.Object.extend({
            initialize: function()
            {
                this.globalState = new GlobalStateModel();
            },

            /** Initialize the layout for the application */
            onBeforeStart: function()
            {
                // Get the resizer going
                this.resizer = new BrowserResizer();

                // Instantiate the root view
                this.rootView = new RootView();

                // The manuscripts page has no state, so we might as well instantiate it
                this.manuscriptsPageView = new ManuscriptsPageView();

                // Render the header
                this.rootView.header.show(new HeaderView());
            },

            /**
             * Display the manuscripts list page
             */
            manuscripts: function()
            {
                this.showContentView(this.manuscriptsPageView);

                // Set the document title to reflect the manuscripts route
                GlobalEventHandler.trigger("ChangeDocumentTitle", "Manuscripts");
            },

            /**
             * Display the detail view for a specific manuscript
             *
             * @param id The manuscript ID
             * @param folio (Optional) The folio to load
             * @param chant (Optional) The chant to load
             */
            manuscriptSingle: function(id, folio, chant)
            {
                var manuscriptView = new ManuscriptIndividualPageView({
                    id: id,
                    folio: folio
                });

                // Get the data for the view and then show it.
                // FIXME(wabain): we need to do this because the manuscriptView can't be re-rendered(?),
                // but needs to be rendered after the data has been loaded. However, that certainly
                // shouldn't be the case
                manuscriptView.getData({
                    success: _.bind(function ()
                    {
                        this.showContentView(manuscriptView);
                    }, this)
                });

                GlobalEventHandler.trigger("ChangeManuscript", id);
                GlobalEventHandler.trigger("ChangeFolio", folio);
                GlobalEventHandler.trigger("ChangeChant", chant);
            },

            /**
             * Display the standalone search view
             *
             * @param query (Optional) The initial query to search
             */
            search: function(query)
            {
                this.showContentView(new SearchPageView({query: query}));
            },

            // TODO: Handle 404 somehow
            notFound: function()
            {
                // jshint devel:true
                console.error('Not found: ' + window.location.href);
            },

            /**
             * Show the view in the mainContent region.
             *
             * @param newView
             */
            showContentView: function(newView)
            {
                this.rootView.mainContent.show(newView, {preventDestroy: this.shouldDestroyMainContentView()});
            },

            /**
             * Determine whether the current view of the main content region should be destroyed
             * when another view is rendered.
             *
             * @returns {boolean}
             */
            shouldDestroyMainContentView: function()
            {
                return this.rootView.mainContent.currentView === this.manuscriptsPageView;
            }
        });
    });