define(["underscore", "backbone", "singletons/GlobalEventHandler", "objects/OpenChantState"],
    function(_, Backbone, GlobalEventHandler, OpenChantState)
    {

        "use strict";

        /**
         * Handles the global state.  Updates URLs and page title
         */
        return Backbone.Model.extend
        ({
            defaults: {
                manuscript: undefined,
                folio: undefined,
                chant: undefined
            },

            initialize: function()
            {
                _.bindAll(this, "setManuscript", "setFolio", "setChant", "restoreOpenChant", "saveOpenChant");

                this.chantStateManager = new OpenChantState();

                this.on('change', this.updateUrl);
                this.on('change:folio', this.restoreOpenChant);
                this.on('change:chant', this.saveOpenChant);

                this.listenTo(GlobalEventHandler, 'ChangeManuscript', this.setManuscript);
                this.listenTo(GlobalEventHandler, 'ChangeFolio', this.setFolio);
                this.listenTo(GlobalEventHandler, 'ChangeChant', this.setChant);
                this.listenTo(GlobalEventHandler, 'ChangeDocumentTitle', this.setDocumentTitle);
            },

            /**
             * On folio change, get the stored chant state for the new folio and set it
             */
            restoreOpenChant: function ()
            {
                /* jshint eqnull:true */

                var manuscript = this.get('manuscript');
                var folio = this.get('folio');

                // Ensure that the manuscript and folio are not null or undefined
                if (manuscript == null || folio == null)
                    return;

                var currentChant = this.get('chant');

                if (currentChant === void 0)
                    currentChant = null;

                var newChant = this.chantStateManager.get(manuscript, folio);

                if (newChant !== currentChant)
                    GlobalEventHandler.trigger('ChangeChant', newChant, {replaceState: true});
            },

            /**
             * On chant change, save the new chant state
             */
            saveOpenChant: function ()
            {
                /* jshint eqnull:true */

                var manuscript = this.get('manuscript');
                var folio = this.get('folio');

                // Ensure that the manuscript and folio are not null or undefined
                if (manuscript == null || folio == null)
                    return;

                this.chantStateManager.set(manuscript, folio, this.get('chant'));
            },

            setManuscript: function(manuscript, params)
            {
                this.set('manuscript', manuscript, {stateChangeParams: params});
            },

            setFolio: function(folio, params)
            {
                this.set('folio', folio, {stateChangeParams: params});
            },

            setChant: function(chant, params)
            {
                this.set('chant', chant, {stateChangeParams: params});
            },

            /**
             * Set the title of the HTML document.
             *
             * @param title
             */
            setDocumentTitle: function(title)
            {
                this.documentTitle = "Cantus Ultimus — " + String(title);
                document.title = this.documentTitle;
            },

            getUrl: function()
            {
                /* jshint eqnull:true */

                var composedUrl = "manuscript/" + this.get('manuscript') + "/";

                // Check that value is not null or undefined
                if (this.get('folio') != null)
                {
                    composedUrl = composedUrl + "?folio=" + this.get('folio');
                }

                if (this.get('chant') != null)
                {
                    composedUrl = composedUrl + "&chant=" + this.get('chant');
                }
                return composedUrl;
            },

            /**
             * Update the url without triggering a page reload
             */
            updateUrl: function(model, options)
            {
                // Don't actually trigger the router!
                Backbone.history.navigate(this.getUrl(), {
                    trigger: false,
                    replace: _.result(options.stateChangeParams, 'replaceState')
                });
            }
        });
    }

);