define(["underscore", "backbone", "singletons/GlobalEventHandler", "objects/OpenChantState"],
    function(_, Backbone, GlobalEventHandler, OpenChantState)
    {

        "use strict";

        var manuscriptStateChannel = Backbone.Radio.channel('manuscript');

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
                this.chantStateManager = new OpenChantState();

                this.on('change:manuscript', this.manuscriptChanged);
                this.on('change:folio', this.folioChanged);
                this.on('change:chant', this.chantChanged);

                this.on('change', this.updateUrl);

                // Proxy model change events to the channel
                _.forEach(_.keys(this.attributes), function (attr)
                {
                    manuscriptStateChannel.reply(attr, _.bind(this.get, this, attr), this);
                    manuscriptStateChannel.reply('set:' + attr, function (value, params)
                    {
                        this.set(attr, value, {stateChangeParams: params});
                    }, this);

                    this.on('change:' + attr, function (model, value)
                    {
                        manuscriptStateChannel.trigger('change:' + attr, value);
                    });
                }, this);

                this.listenTo(GlobalEventHandler, 'ChangeDocumentTitle', this.setDocumentTitle);
            },

            onDestroy: function ()
            {
                // Remove all callbacks from this object
                manuscriptStateChannel.stopReplying(null, null, this);
            },

            /**
             * On manuscript change, reset the folio if it hasn't been explicitly set
             */
            manuscriptChanged: function ()
            {
                if (!this.hasChanged('folio'))
                {
                    this.set('folio', null);
                }
            },

            /**
             * On folio change, get the stored chant state for the new folio and set it
             */
            folioChanged: function ()
            {
                /* jshint eqnull:true */

                // If the chant was explicitly set in this round of updates then don't
                // change it here (the chantChanged callback will handle the relevant
                // state)
                if (this.hasChanged('chant'))
                    return;

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
                    this.set('chant', newChant, {replaceState: true});
            },

            /**
             * On chant change, save the new chant state
             */
            chantChanged: function ()
            {
                /* jshint eqnull:true */

                var manuscript = this.get('manuscript');
                var folio = this.get('folio');

                // Ensure that the manuscript and folio are not null or undefined
                if (manuscript == null || folio == null)
                    return;

                this.chantStateManager.set(manuscript, folio, this.get('chant'));
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