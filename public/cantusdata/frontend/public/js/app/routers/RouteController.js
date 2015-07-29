define(["underscore",
        "backbone",
        "marionette",
        "link-watcher",
        "config/GlobalVars",
        "models/ManuscriptStateModel",
        "models/Manuscript",
        "views/RootView",
        "views/HeaderView",
        "views/ManuscriptsPageView",
        "views/ManuscriptIndividualPageView",
        "views/SearchPageView",
        "singletons/GlobalEventHandler"],
    function(_,
             Backbone,
             Marionette,
             LinkWatcher,
             GlobalVars,
             ManuscriptStateModel,
             Manuscript,
             RootView,
             HeaderView,
             ManuscriptsPageView,
             ManuscriptIndividualPageView,
             SearchPageView,
             GlobalEventHandler)
    {
        "use strict";

        return Marionette.Object.extend({
            initialize: function(options)
            {
                this.rootView = this.getOption('rootView', options);

                // Support maintaining arbitrary state for the active route (by default just
                // a fragment)
                this.routeState = null;
                this.listenTo(Backbone.history, 'route', function ()
                {
                    if (!this.routeState || this.routeState.fragment !== Backbone.history.fragment)
                    {
                        this.resetRouteState();
                    }
                });

                this.initialRouteComplete = false;
                this.listenToOnce(Backbone.history, 'route', function ()
                {
                    this.initialRouteComplete = true;
                });

                // Change the document title when
                this.listenTo(GlobalEventHandler, 'ChangeDocumentTitle', this.setDocumentTitle);
            },

            /** Initialize the layout for the application */
            onBeforeStart: function()
            {
                // The manuscripts page has no state, so we might as well instantiate it
                this.manuscriptsPageView = new ManuscriptsPageView();

                // Navigate to clicked links
                LinkWatcher.onLinkClicked(document.body, function (event, info)
                {
                    if (info.isLocalNavigation && !info.isFragmentNavigation)
                    {
                        event.preventDefault();
                        Backbone.history.navigate(info.relativePath, {trigger: true});
                    }
                }, {rootHref: GlobalVars.siteUrl});
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
                // Update the route state
                if (!(this.routeState && this.routeState.model instanceof ManuscriptStateModel))
                {
                    this.resetRouteState();
                    this.routeState.model = new ManuscriptStateModel();
                }
                else
                {
                    this.routeState.fragment = Backbone.history.fragment;
                }

                var prevId = this.routeState.model.get('manuscript');

                this.routeState.model.set({
                    manuscript: id,
                    folio: folio,
                    chant: chant
                });

                // Don't reload the view if the manuscript has not changed
                if (prevId === id)
                    return;

                var manuscript = new Manuscript({id: id});

                var manuscriptView = new ManuscriptIndividualPageView({
                    model: manuscript
                });

                // Get the data for the view and then show it.
                // FIXME(wabain): we need to do this because the manuscriptView can't be re-rendered(?),
                // but needs to be rendered after the data has been loaded. However, that certainly
                // shouldn't be the case
                manuscript.fetch({
                    success: _.bind(function ()
                    {
                        this.showContentView(manuscriptView);
                    }, this)
                });
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

            notFound: function()
            {
                if (!this.initialRouteComplete)
                {
                    // If this is the initial route then we've probably done something wrong.
                    // We can't trigger a browser reload since that would probably kick off an
                    // infinite loop.

                    // jshint devel:true
                    console.error('Started at unrecognized page: %s (fragment %s)', window.location.href,
                        Backbone.history.fragment);
                }
                else if (Backbone.history._hasPushState)
                {
                    // Trigger a browser reload
                    Backbone.history.location.href = Backbone.history.location.href;
                }
                else
                {
                    // Send the browser to the page for the current fragment
                    window.location = GlobalVars.siteUrl + Backbone.history.fragment;
                }
            },

            resetRouteState: function ()
            {
                if (this.routeState && this.routeState.model)
                {
                    this.routeState.model.destroy();
                }

                this.routeState = {
                    fragment: Backbone.history.fragment
                };
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
            },

            /**
             * Set the title of the HTML document.
             *
             * @param title
             */
            setDocumentTitle: function(title)
            {
                if (title)
                    document.title = "Cantus Ultimus — " + title;
                else
                    document.title = "Cantus Ultimus";
            }
        });
    });