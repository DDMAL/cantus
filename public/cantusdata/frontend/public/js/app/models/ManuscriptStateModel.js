define(["underscore", "jquery", "backbone", "objects/OpenChantState", "models/Manuscript"],
    function(_, $, Backbone, OpenChantState, Manuscript)
    {

        "use strict";

        var manuscriptStateChannel = Backbone.Radio.channel('manuscript');

        /**
         * Handles the manuscript state (i.e. the selected manuscript, folio, and
         * chant and the transition invariants between them), exposing the changes
         * using the 'manuscript' channel.
         */
        return Backbone.Model.extend({
            defaults: {
                manuscript: undefined,
                folio: undefined,
                chant: undefined
            },

            initialize: function()
            {
                this.chantStateManager = new OpenChantState();
                this.manuscriptModel = null;

                this.on('change:manuscript', this.manuscriptChanged);
                this.on('change:folio', this.folioChanged);
                this.on('change:chant', this.chantChanged);

                this.on('change', this.publishChanges);
                this.on('change', this.updateUrl);

                manuscriptStateChannel.reply('model:manuscript', this.getManuscriptModel, this);

                // Proxy model getters and setters to the channel
                _.forEach(_.keys(this.attributes), function (attr)
                {
                    manuscriptStateChannel.reply(attr, _.bind(this.get, this, attr), this);

                    manuscriptStateChannel.reply('set:' + attr, function (value, params)
                    {
                        this.set(attr, value, {stateChangeParams: params});
                    }, this);
                }, this);

                this.on('destroy', this.onDestroy);
            },

            onDestroy: function ()
            {
                // Stop replying to state requests
                manuscriptStateChannel.stopReplying(null, null, this);
            },

            /**
             * On manuscript change, reset the folio if it hasn't been explicitly set
             */
            manuscriptChanged: function ()
            {
                this.manuscriptModel = null;

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
             * Publish changes to the manuscript channel. If the manuscript
             * has changed, wait for the manuscript model to load first.
             */
            publishChanges: function ()
            {
                if (this.hasChanged('manuscript'))
                {
                    var changed = this.changedAttributes();
                    var self = this;

                    // FIXME: handle load failures somehow?
                    this.loadManuscriptModel().always(function ()
                    {
                        self.triggerChangeEvents(changed);
                    });
                }
                else
                {
                    this.triggerChangeEvents(this.changed);
                }
            },

            /**
             * Trigger change events on the channel for each of the attributes
             * in the changed hash
             * @param changed
             */
            triggerChangeEvents: function (changed)
            {
                _.forEach(changed, function (value, attr)
                {
                    manuscriptStateChannel.trigger('change:' + attr, value);
                }, this);
            },

            getManuscriptModel: function ()
            {
                return this.manuscriptModel;
            },

            /**
             * Load the model for the current manuscript from the server.
             * @returns {jQuery.Promise} a promise which resolves once the manuscript model is synced
             */
            loadManuscriptModel: function ()
            {
                // jshint eqnull:true

                // If there is no manuscript, return a promise
                // which resolves to null
                if (this.get('manuscript') == null)
                    return $.when(null);

                var deferred = $.Deferred();
                var model = new Manuscript({id: this.get('manuscript')});
                var self = this;

                model.fetch({
                    success: function ()
                    {
                        self.manuscriptModel = model;
                        deferred.resolve(model);
                        self.trigger('load:manuscript', model);
                    },
                    error: function (model, resp)
                    {
                        deferred.reject(resp);

                        // FIXME: what's a better thing to do here?
                        self.trigger('load:manuscript', null);
                    }
                });

                return deferred.promise();
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