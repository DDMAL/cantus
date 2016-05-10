import Marionette from "marionette";
import Radio from "backbone.radio";

import SearchView from "search/SearchView";
import ChantSearchProvider from "search/chant-search/ChantSearchProvider";

import ModalView from "./ModalView";

import subheadTemplate from './navbar-subhead.template.html';

var navChannel = Radio.channel('navigation');

/**
 * Add JS enhancements to the page header.
 */
export default Marionette.LayoutView.extend({
    el: '#page-header',
    template: false,

    // Subviews
    searchView: null,
    searchModalView: null,

    regions: {
        pageTitle: '#page-title',
        searchModalRegion: '#search-modal'
    },

    ui: {
        siteBrand: '.navbar-brand',
        navButton: '.navbar-toggle',
        searchModalLink: '.search-modal-link',
        navLinks: '#top-menu li > a'
    },

    events: {
        'click @ui.navButton': 'toggleNavigationDrawer'
    },

    initialize: function()
    {
        navChannel.reply('set:navbarTitle', this.updateNavbarTitle, this);

        // The search view that we will shove into the modal box
        this.searchView = new SearchView({
            providers: [new ChantSearchProvider({
                additionalResultFields: ['manuscript', 'genre', 'mode', 'feast', 'office']
            })]
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
        navChannel.request('toggle:menu');
    },

    /**
     * When the global navbarTitle changes, update the pageTitle region
     * to display it
     *
     * @param title
     */
    updateNavbarTitle: function (title)
    {
        if (title)
        {
            this.pageTitle.show(new Marionette.ItemView({
                tagName: 'span',
                template: subheadTemplate,
                templateHelpers: {
                    subhead: title
                }
            }));

            this.ui.siteBrand.removeClass('no-subhead');
        }
        else
        {
            this.pageTitle.empty();
            this.ui.siteBrand.addClass('no-subhead');
        }
    },

    onRender: function ()
    {
        var searchModalAttrs = {
            'data-toggle': 'modal',
            href: '#myModal'
        };

        // Dynamically make the search link a modal
        this.ui.searchModalLink.attr(searchModalAttrs);

        // Get the nav links from the DOM and add them to the collection.
        // The advantage of doing things this way is that it makes it possible to
        // provide a simple, mobile-friendly, JavaScript-free default.
        var navLinkCollection = this.collection;
        var searchModalLinkElem = this.ui.searchModalLink[0];

        this.ui.navLinks.each(function ()
        {
            var profile = {content: this.textContent, attr: {href: this.href}};

            // Special case: The search link will become a modal target
            if (this === searchModalLinkElem)
                profile.attr = searchModalAttrs;

            navLinkCollection.add(profile);
        });

        this.searchModalRegion.show(this.searchModalView, {preventDestroy: true});
    },

    onDestroy: function ()
    {
        this.searchModalView.destroy();
    }
});
