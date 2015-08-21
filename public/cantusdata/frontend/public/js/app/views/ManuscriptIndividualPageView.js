define(['jquery',
        'underscore',
        'marionette',
        'diva',
        "models/Manuscript",
        "views/FolioView",
        "views/DivaView",
        "views/SearchView",
        "views/ManuscriptDataPopoverView",
        "views/ChantSearchProvider",
        "views/NotationSearchProvider"],
function($,
         _,
         Marionette,
         diva,
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

    // Subviews
    divaView: null,
    folioView: null,

    ui: {
        toolbarRow: '#toolbar-row',
        manuscriptInfo: '#manuscript-info-popover',
        manuscriptInfoButton: '#manuscript-info-popover button',
        resizer: '#manuscript-data-container .resizer',
        divaColumn: "#diva-column",
        manuscriptDataColumn: '#manuscript-data-column'
    },

    // FIXME(wabain): use inserted.bs.popover after updating bootstrap
    events: {
        'mousedown @ui.resizer': 'startResizing',
        'shown.bs.popover @ui.manuscriptInfoButton': 'instantiatePopoverView',
        'hidden.bs.popover @ui.manuscriptInfoButton': 'destroyPopoverView'
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

        this.chantSearchProvider.setRestriction('manuscript', '"' + this.model.get("siglum") + '"');

        this.notationSearchProvider = new NotationSearchProvider({
            divaView: this.divaView,
            manuscript: this.model
        });

        this.searchView = new SearchView({
            providers: [this.chantSearchProvider, this.notationSearchProvider]
        });
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

    startResizing: function (event)
    {
        event.preventDefault();

        // Set up
        var divaColumn = this.ui.divaColumn,
            panes = this.ui.manuscriptDataColumn,
            initialX = event.clientX,
            initialWidth = panes.width();

        // Support for the various event capture APIs is too spotty, so just throw an overlay
        // over everything and capture events based on that; since the overlay should be above
        // everything else, we should be able to ensure that events bubble up to the window.
        var $window = $(window);
        var overlay = $('<div class="dragging-overlay col-resize-cursor">');

        overlay.appendTo(document.body);

        var executeResize = function (event)
        {
            var difference = initialX - event.clientX;
            var newWidthPercentage = (initialWidth + difference) / (divaColumn.width() + panes.width()) * 100;

            // FIXME(wabain): Handle min-width issues
            divaColumn.css('width', (100 - newWidthPercentage) + '%');
            panes.css('width', newWidthPercentage + '%');

            updateDivaSize();
        };

        var updateDivaSize = _.throttle(function ()
        {
            diva.Events.publish("PanelSizeDidChange");
        }, 250);

        var stopResizing = function ()
        {
            overlay.remove();
            $window.off('mousemove', executeResize);
        };

        $window.on('mousemove', executeResize);
        $window.one('mouseup', stopResizing);
    },

    instantiatePopoverView: function ()
    {
        this.popoverView = new ManuscriptDataPopoverView({
            el: this.ui.manuscriptInfo.find('.popover')
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

    onShow: function()
    {
        this.ui.manuscriptInfoButton.popover({
            content: this.getPopoverContent,
            html: true
        });

        // FIXME: Is there a nicer way to set this?
        this.divaView.toolbarParentObject = this.ui.toolbarRow;

        // Move the manuscript info button into the Diva toolbar
        // FIXME: this is not a very good way to do this
        this.listenToOnce(this.divaView, 'loaded:viewer', function ()
        {
            this.ui.manuscriptInfo.prependTo(this.ui.toolbarRow.find('.diva-tools-right'));
            this.triggerMethod('recalculate:size');
            this.divaView.triggerMethod('recalculate:size');
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
