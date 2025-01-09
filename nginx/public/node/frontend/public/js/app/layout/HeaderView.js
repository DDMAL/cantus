import Marionette from "marionette";
import Radio from "backbone.radio";

import SearchView from "search/SearchView";
import ChantSearchProvider from "search/chant-search/ChantSearchProvider";
import AboutVolpianoView from "search/chant-search/AboutVolpianoView";

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
        searchModalRegion: '#search-modal',
        aboutVolpianoModalRegion: '#about-volpiano-modal'
    },

    ui: {
        siteBrand: '.navbar-brand',
        navButton: '.navbar-toggler',
        navLinks: '#top-menu > a'
    },

    events: {
        'click @ui.navButton': 'toggleNavigationDrawer'
    },

    initialize: function () {
        navChannel.reply('set:navbarTitle', this.updateNavbarTitle, this);

        // The search view that we will shove into the modal box
        this.searchView = new SearchView({
            providers: [new ChantSearchProvider({
                additionalResultFields: ['manuscript', 'genre', 'mode', 'feast', 'office']
            })]
        });

        // The modal box for the search pop-up
        this.searchModalView = new ModalView({ title: "Search", view: this.searchView, modalId: "searchModal" });

        this.aboutVolpianoView = new AboutVolpianoView();
        this.aboutVolpianoModalView = new ModalView({ title: "About Volpiano", view: this.aboutVolpianoView, modalId: "aboutVolModal" });
    },

    /**
     * Expand the side menu on click
     * @param event
     */
    toggleNavigationDrawer: function (event) {
        event.preventDefault();
        navChannel.request('toggle:menu');
    },

    /**
     * When the global navbarTitle changes, update the pageTitle region
     * to display it
     *
     * @param title
     */
    updateNavbarTitle: function (title) {
        if (title) {
            this.pageTitle.show(new Marionette.ItemView({
                tagName: 'span',
                template: subheadTemplate,
                templateHelpers: {
                    subhead: title
                }
            }));

            this.ui.siteBrand.removeClass('no-subhead');
        }
        else {
            this.pageTitle.empty();
            this.ui.siteBrand.addClass('no-subhead');
        }
    },

    onRender: function () {
        // Get the nav links from the DOM and add them to the collection.
        // The advantage of doing things this way is that it makes it possible to
        // provide a simple, mobile-friendly, JavaScript-free default.
        var navLinkCollection = this.collection;

        this.ui.navLinks.each(function () {
            // Get text content and all attributes except the class attribute from the link
            var attrs = {};
            for (var i = 0; i < this.attributes.length; i++) {
                var attr = this.attributes[i];
                if (attr.nodeName != 'class') {
                    attrs[attr.nodeName] = attr.nodeValue;
                }
            }

            var profile = { content: this.textContent, attr: attrs };

            navLinkCollection.add(profile);
        });

        this.searchModalRegion.show(this.searchModalView, { preventDestroy: true });
        this.aboutVolpianoModalRegion.show(this.aboutVolpianoModalView, { preventDestroy: true });
    },

    onDestroy: function () {
        this.searchModalView.destroy();
        this.aboutVolpianoModalView.destroy();
    }
});
