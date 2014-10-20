define(["jquery", "backbone", "singletons/GlobalEventHandler"],
    function($, Backbone, GlobalEventHandler) {

        "use strict";

        /**
         * Handles the global state.  Updates URLs.
         */
        return Backbone.Model.extend
        ({
            manuscript: undefined,
            folio: undefined,
            chant: undefined,

            initialize: function()
            {
                _.bindAll(this, "setManuscript", "setFolio", "setChant", "silentUrlUpdate");
                this.listenTo(GlobalEventHandler, 'ChangeManuscript', this.setManuscript);
                this.listenTo(GlobalEventHandler, 'ChangeFolio', this.setFolio);
                this.listenTo(GlobalEventHandler, 'ChangeChant', this.setChant);
                this.listenTo(GlobalEventHandler, 'SilentUrlUpdate', this.silentUrlUpdate);
            },

            setManuscript: function(manuscript)
            {
                this.manuscript = manuscript;
            },

            setFolio: function(folio)
            {
                this.folio = folio;
            },

            setChant: function(chant)
            {
                this.chant = chant;
            },

            getUrl: function()
            {
                var composed_url = "manuscript/" + this.manuscript + "/";
                if (this.folio !== undefined && this.folio !== null)
                {
                    composed_url = composed_url + "?folio=" + this.folio;
                }
                if (this.chant !== undefined && this.chant !== null)
                {
                    composed_url = composed_url + "&chant=" + this.chant;
                }
                return composed_url;
            },

            silentUrlUpdate: function()
            {
                console.log("silentUrlUpdate()");
                // Don't actually trigger the router!
                Backbone.history.navigate(this.getUrl(), {trigger: false});
            }
        });
    }

);