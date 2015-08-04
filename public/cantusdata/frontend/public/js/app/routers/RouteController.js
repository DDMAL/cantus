define(["underscore",
        "backbone",
        "marionette",
        "link-watcher",
        "qs",
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
             Qs,
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
             * @param query The query string
             */
            manuscriptSingle: function(id, query)
            {
                var params = Qs.parse(query);

                var folio = _.has(params, 'folio') ? params.folio : null;
                var chant = _.has(params, 'chant') ? params.chant : null;

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

                // Don't reload the whole view if the manuscript has not changed
                if (prevId === id)
                {
                    this.routeState.model.set({
                        folio: folio,
                        chant: chant
                    });

                    return;
                }

                /* Render the view once the manuscript model has been loaded from the server.
                 *
                 * FIXME: We do things this way (instantiating the page view with a loaded model after
                 * each manuscript change) for two reasons:
                 *
                 * 1. The views aren't set up to be instantiated and rendered without a loaded model
                 * 2. Some of the views can't handle changes to the manuscript
                 *
                 * Fixing (1) probably isn't worth it, but fixing (2) might be
                 */
                this.listenToOnce(this.routeState.model, 'load:manuscript', function (model)
                {
                    this.showContentView(new ManuscriptIndividualPageView({
                        model: model
                    }));
                });

                this.routeState.model.set({
                    manuscript: id,
                    folio: folio,
                    chant: chant
                });
            },

            /**
             * Display the standalone search view
             *
             * @param queryString The query string
             */
            search: function(queryString)
            {
                var query = Qs.parse(queryString).q;
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