define(["jquery", "backbone", "singletons/GlobalEventHandler", "objects/OpenChantState"],
    function($, Backbone, GlobalEventHandler, OpenChantState) {

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
                _.bindAll(this, "setManuscript", "setFolio", "setChant");

                this.on('change', this.updateUrl);

                this.listenTo(GlobalEventHandler, 'ChangeManuscript', this.setManuscript);
                this.listenTo(GlobalEventHandler, 'ChangeFolio', this.setFolio);
                this.listenTo(GlobalEventHandler, 'ChangeChant', this.setChant);
                this.listenTo(GlobalEventHandler, 'ChangeDocumentTitle', this.setDocumentTitle);
            },

            setManuscript: function(manuscript)
            {
                this.set('manuscript', manuscript);
            },

            setFolio: function(folio)
            {
                this.set('folio', folio);
            },

            setChant: function(chant)
            {
                this.set('chant', chant);
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

                var composed_url = "manuscript/" + this.get('manuscript') + "/";

                // Check that value is not null or undefined
                if (this.get('folio') != null)
                {
                    composed_url = composed_url + "?folio=" + this.get('folio');
                }

                if (this.get('chant') != null)
                {
                    composed_url = composed_url + "&chant=" + this.get('chant');
                }
                return composed_url;
            },

            /**
             * Update the url without triggering a page reload
             */
            updateUrl: function()
            {
                // Don't actually trigger the router!
                Backbone.history.navigate(this.getUrl(), {trigger: false});
            }
        });
    }

);