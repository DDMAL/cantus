define(["marionette",
        "backbone.radio",
        "singletons/NavigationManager",
        "views/SearchView",
        "views/ChantSearchProvider",
        "views/ModalView"],
    function(Marionette, Radio, NavigationManager, SearchView, ChantSearchProvider, ModalView)
    {
        "use strict";

        var sidenavChannel = Radio.channel('sidenav');

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
                navButton: '.navbar-toggle',
                searchModalLink: '.search-modal-link',
                navLinks: '#top-menu li > a'
            },

            events: {
                'click @ui.navButton': 'toggleNavigationDrawer'
            },

            initialize: function()
            {
                // The search view that we will shove into the modal box
                this.searchView = new SearchView({
                    providers: [new ChantSearchProvider({showManuscriptName: true})]
                });

                // The modal box for the search pop-up
                this.searchModalView = new ModalView({title: "Search", view: this.searchView});
            },

            /**
             * Expand the side menu on click
             * @param event
             */
            toggleNavigationDrawer: function (event)
            {
                event.preventDefault();
                sidenavChannel.request('toggle');
            },

            onRender: function ()
            {
                // Extract nav links from the DOM and move them into the navigation manager.
                // The advantage of doing things this way is that it makes it possible to
                // provide a simple, mobile-friendly, JavaScript-free default.
                if (this.ui.navLinks.length > 0)
                {
                    var searchModalLinkElem = this.ui.searchModalLink[0];

                    this.ui.navLinks.remove();
                    this.ui.navLinks.each(function ()
                    {
                        var profile = {content: this.textContent, attr: {href: this.href}};

                        // Special case: The search link will become a modal target
                        if (this === searchModalLinkElem)
                        {
                            profile.attr['data-toggle'] = 'modal';
                            profile.attr.href = '#myModal';
                        }

                        NavigationManager.navItems.add(profile);
                    });

                    // Update the relevant cached jQuery objects
                    this.ui.navLinks = this.$(this.ui.navLinks.selector);
                    this.ui.searchModalLink = this.$(this.ui.searchModalLink.selector);
                }

                this.searchModalRegion.show(this.searchModalView, {preventDestroy: true});
            },

            onDestroy: function ()
            {
                this.searchModalView.destroy();
            }
        });
    });
