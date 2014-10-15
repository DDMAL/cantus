//var Folio = require(["models/Folio"]);
//var CantusAbstractView = require(["views/CantusAbstractView"]);
//var ChantCollectionView = require(["views/ChantCollectionView"]);

define( ['App', 'backbone', 'marionette', 'jquery', "models/Folio", "views/CantusAbstractView", "views/ChantCollectionView"],
    function(App, Backbone, Marionette, $, Folio, CantusAbstractView, ChantCollectionView, template) {

        /**
         * Provide an alert message to the user.
         */
        return CantusAbstractView.extend
        ({
            /**
             * customNumber is the folio number that we actually render.
             */
            customNumber: 0,

            // Subviews
            chantCollectionView: null,

            /**
             *
             *
             * @param {type} options
             * @returns null
             */
            initialize: function(options)
            {
                _.bindAll(this, 'render', 'afterFetch', 'assignChants');
                this.template= _.template($('#folio-template').html());
                // This can handle situations where the first folio
                // doesn't have a url but subsequent ones do.
                if (options && options.url)
                {
                    this.setUrl(options.url);
                }
                else
                {
                    this.model = new Folio();
                    this.listenTo(this.model, 'sync', this.afterFetch);
                }
                this.chantCollectionView = new ChantCollectionView();
            },

            remove: function()
            {
                this.chantCollectionView.remove();

                // Deal with the event listeners
                this.stopListening();
                this.undelegateEvents();
            },

            /**
             * Set the model URL.
             *
             * @param url
             */
            setUrl: function(url)
            {
                this.model = new Folio(url);
                this.listenTo(this.model, 'sync', this.afterFetch);
            },

            /**
             * Set the parameter that overrides the number that's rendered to the
             * screen.
             *
             * @param number
             */
            setCustomNumber: function(number)
            {
                this.customNumber = number;
            },

            /**
             * Fetch the latest version of the model.
             */
            update: function()
            {
                this.model.fetch();
            },

            /**
             * If the model is empty, un-render the view.  Otherwise, assign
             * the chants and render the view.
             */
            afterFetch: function()
            {
                this.assignChants();
                this.render();
            },

            /**
             * Rebuild the list of chants
             */
            assignChants: function()
            {
                // We are going to query this data from SOLR because it's faster.
                // So we need the manuscript siglum and folio name.
                // We need to handle the data differently depending on whether
                // we're getting the information from Django or Solr.
                var folio_id;
                if (this.model.get("item_id"))
                {
                    folio_id = this.model.get("item_id");
                }
                else
                {
                    folio_id = this.model.get("id");
                }

                if (folio_id !== undefined)
                {
                    // Compose the url
                    var composedUrl = siteUrl + "chant-set/folio/" + folio_id + "/";
                    // Build a new view with the new data
                    this.chantCollectionView.setUrl(composedUrl);
                }
                else
                {
                    this.chantCollectionView.resetCollection();
                }
            },

            render: function()
            {
                $(this.el).html(this.template(
                    {
                        number: this.customNumber,
                        model: this.model.toJSON()
                    }
                ));
                this.renderChantCollectionView();
                globalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            },

            /**
             * Render the collection of chants.
             */
            renderChantCollectionView: function()
            {
                if (this.chantCollectionView !== null)
                {
                    this.assign(this.chantCollectionView, '#chant-list');
                }
            }
        });
    });