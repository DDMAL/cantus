define(['underscore',
        'marionette',
        "models/Manuscript",
        "views/FolioView",
        "views/DivaView",
        "views/SearchView",
        "views/ManuscriptDataPopoverView",
        "views/ChantSearchProvider",
        "views/NotationSearchProvider"],
function(_,
         Marionette,
         Manuscript,
         FolioView,
         DivaView,
         SearchView,
         ManuscriptDataPopoverView,
         ChantSearchProvider,
         NotationSearchProvider)
{

"use strict";

/**
 * This page shows an individual manuscript.  You get a nice diva viewer
 * and you can look through the chant info.
 *
 * @type {*|void}
 */
return Marionette.LayoutView.extend
({
    template: '#manuscript-template',

    searchView: null,
    popoverContent: null,

    initialViewPortSize: null,

    // Subviews
    divaView: null,
    folioView: null,

    ui: {
        manuscriptTitleContainer: '#manuscript-title-container',
        manuscriptTitlePopoverLink: '#manuscript-title-popover-link'
    },

    // FIXME(wabain): use inserted.bs.popover after updating bootstrap
    events: {
        'shown.bs.popover @ui.manuscriptTitlePopoverLink': 'instantiatePopoverView',
        'hidden.bs.popover @ui.manuscriptTitlePopoverLink': 'destroyPopoverView'
    },

    regions: {
        divaViewRegion: "#diva-column",
        folioViewRegion: "#folio",
        searchViewRegion: "#manuscript-search"
    },

    behaviors: {
        resize: {
            target: '#manuscript-data-container',
            action: 'onWindowResized'
        },

        pageConfig: {
            elements: {
                html: {
                    styles: {
                        'min-width': 880
                    }
                },

                // FIXME(wabain): Figure out if we really need to do this at all
                'meta[name=viewport]': {
                    attributes: {
                        content: function ()
                        {
                            return $(window).width() <= 880 ? 'width=880, user-scalable=no' : 'width=device-width';
                        }
                    }
                },

                '.navbar': {
                    styles: {
                        'margin-bottom': 0
                    }
                }
            }
        }
    },

    initialize: function ()
    {
        _.bindAll(this, 'getPopoverContent');

        // Build the subviews
        this.divaView = new DivaView({
            siglum: this.model.get("siglum_slug")
        });
        this.folioView = new FolioView();

        this.chantSearchProvider = new ChantSearchProvider({
            additionalResultFields: ['mode', 'genre']
        });

        this.notationSearchProvider = new NotationSearchProvider({divaView: this.divaView});

        // Propagate the initial, passed-in model state
        this.afterFetch();

        this.searchView = new SearchView({
            providers: [this.chantSearchProvider, this.notationSearchProvider]
        });

        this.listenTo(this.model, 'change', this.afterFetch);
    },

    /**
     * Marionette method called automatically before the destroy event happens.
     */
    onBeforeDestroy: function()
    {
        this.divaView.destroy();
        this.searchView.destroy();
        this.folioView.destroy();
        this.destroyPopoverView();
    },

    instantiatePopoverView: function ()
    {
        this.popoverView = new ManuscriptDataPopoverView({
            el: this.ui.manuscriptTitleContainer.find('.popover')
        });
    },

    destroyPopoverView: function ()
    {
        if (this.popoverView)
        {
            this.popoverView.destroy();
            this.popoverView = null;
        }
    },

    /**
     * Get the HTML content for the manuscript data popover, generating it from a template if it has not
     * already been initialized.
     *
     * @returns {string}
     */
    getPopoverContent: function ()
    {
        if (!this.popoverContent)
            this.popoverContent = Marionette.TemplateCache.get('#manuscript-data-template')(this.serializeData());

        return this.popoverContent;
    },

    // FIXME(wabain): At the moment this can only feasibly be called during view initialization
    afterFetch: function()
    {
        // Set the search view to only search this manuscript
        this.chantSearchProvider.setRestriction('manuscript', '"' + this.model.get("siglum") + '"');
        this.notationSearchProvider.setManuscript(this.model);

        this.divaView.setManuscript(this.model.get("siglum_slug"));
    },

    onShow: function()
    {
        this.ui.manuscriptTitlePopoverLink.popover({
            content: this.getPopoverContent,
            html: true
        });

        // Render subviews
        this.divaViewRegion.show(this.divaView, {preventDestroy: true});
        this.folioViewRegion.show(this.folioView, {preventDestroy: true});
        this.searchViewRegion.show(this.searchView);
    },

    onWindowResized: function ()
    {
        this.triggerMethod('configure:page', 'meta[name=viewport]');
    }
});
});
