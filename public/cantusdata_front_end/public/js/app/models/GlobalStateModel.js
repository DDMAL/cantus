define(["jquery", "backbone", "singletons/GlobalEventHandler", "objects/OpenChantState"],
    function($, Backbone, GlobalEventHandler, OpenChantState) {

        "use strict";

        /**
         * Handles the global state.  Updates URLs and page title
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
                this.listenTo(GlobalEventHandler, 'ChangeDocumentTitle', this.setDocumentTitle);
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
                // Don't actually trigger the router!
                Backbone.history.navigate(this.getUrl(), {trigger: false});
            }
        });
    }

);