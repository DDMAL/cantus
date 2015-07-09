define(["marionette",
        "views/SearchView",
        "views/ModalView",
        "singletons/GlobalEventHandler"],
    function(Marionette, SearchView, ModalView, GlobalEventHandler)
    {
        "use strict";

        /**
         * Provide an alert message to the user.
         */
        return Marionette.LayoutView.extend({
            template: '#header-template',

            // Subviews
            searchView: null,
            searchModalView: null,

            regions: {
                searchModalRegion: '#search-modal'
            },

            ui: {
                searchModalLink: '.search-modal-link'
            },

            initialize: function()
            {
                // The search view that we will shove into the modal box
                this.searchView = new SearchView({showManuscriptName: true});

                // The modal box for the search pop-up
                this.searchModalView = new ModalView({title: "Search", view: this.searchView});
            },

            onRender: function ()
            {
                // Turn the search link into a modal target dynamically
                this.ui.searchModalLink.attr({'data-toggle': 'modal', href: '#myModal'});

                this.searchModalRegion.show(this.searchModalView, {preventDestroy: true});
                GlobalEventHandler.trigger("renderView");
            }
        });
    });
