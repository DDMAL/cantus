import $ from 'jquery';
import _ from 'underscore';
import Radio from 'backbone.radio';
import Marionette from 'marionette';
import diva from 'diva';

import SearchView from "search/SearchView";
import ChantSearchProvider from "search/chant-search/ChantSearchProvider";
import OMRSearchProvider from "search/omr-search/OMRSearchProvider";

import FolioView from "./folio/FolioView";
import DivaView from "./DivaView";
import ManuscriptDataPopoverView from "./ManuscriptDataPopoverView";

var manuscriptStateChannel = Radio.channel('manuscript');

/**
 * This page shows an individual manuscript.  You get a nice diva viewer
 * and you can look through the chant info.
 *
 * @type {*|void}
 */
export default Marionette.LayoutView.extend({
    template: '#manuscript-template',

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
        }
    },

    initialize: function ()
    {
        _.bindAll(this, 'getPopoverContent');

        this.popoverContent = null;
        this._viewportContent = null;
    },

    onBeforeDestroy: function()
    {
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

            updateDivaSize(); // eslint-disable-line no-use-before-define
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

    onRender: function()
    {
        this._configurePageLayout();

        // Initialize the Diva view
        var divaView = new DivaView({
            siglum: this.model.get("siglum_slug"),
            toolbarParentObject: this.ui.toolbarRow
        });

        // Move the manuscript info button into the Diva toolbar
        // FIXME: this is not a very good way to do this
        this.listenToOnce(divaView, 'loaded:viewer', function ()
        {
            this.ui.manuscriptInfo.prependTo(this.ui.toolbarRow.find('.diva-tools-right'));
            this.triggerMethod('recalculate:size');
            divaView.triggerMethod('recalculate:size');
        });

        // Initialize the search view
        var chantSearchProvider = new ChantSearchProvider({
            additionalResultFields: ['genre', 'mode', 'feast', 'office', 'position']
        });

        chantSearchProvider.setRestriction('manuscript', '"' + this.model.get("siglum") + '"');

        var notationSearchProvider = new OMRSearchProvider({
            divaView: divaView,
            manuscript: this.model
        });

        var searchTerm = manuscriptStateChannel.request('search');
        var searchView = new SearchView({
            searchTerm: searchTerm,
            providers: [chantSearchProvider, notationSearchProvider]
        });

        // Set the global search state when the search term changes
        this.listenTo(searchView, 'search', function (search)
        {
            if (search.type === 'all' && search.query === '')
                search = null;

            manuscriptStateChannel.request('set:search', search, {replaceState: true});
        });

        // Initialize the manuscript info button
        this.ui.manuscriptInfoButton.popover({
            content: this.getPopoverContent,
            html: true
        });

        // Render the subviews
        this.folioViewRegion.show(new FolioView());
        this.searchViewRegion.show(searchView);

        // We can't show the Diva view until this view has been attached to the DOM
        // See https://github.com/DDMAL/diva.js/issues/273
        //
        // FIXME: For reasons that aren't clear to me, onDomRefresh doesn't fire consistently
        // on initialization in the DivaView, so we wait for DOM Refresh before showing the
        // view here. Maybe check if that is resolved after updating Marionette?
        this.once('dom:refresh', function ()
        {
            this.divaViewRegion.show(divaView);

            // Diva inserts its own viewport on initialization, so we need to reset it
            // TODO: Take this out after upgrading to Diva 4.0
            this._viewportContent = null;
            this._updateViewport();
        });
    },

    _configurePageLayout: function ()
    {
        var html = $('html');
        var navbar = $('.navbar');
        var viewport = $('meta[name=viewport]');

        // Retain original values
        var initialHtmlMinWidth = html.css('min-width');
        var initialNavbarMargin = navbar.css('margin-bottom');
        var initialViewportContent = viewport.attr('content');

        this._viewportContent = initialViewportContent;

        // Set view-specific values
        html.css('min-width', 880);
        navbar.css('margin-bottom', 0);
        this._updateViewport();

        // Restore original values on view destruction
        this.once('destroy', function ()
        {
            html.css('min-width', initialHtmlMinWidth);
            navbar.css('margin-bottom', initialNavbarMargin);
            this._setViewport(initialViewportContent);
        });
    },

    /**
     * Update the viewport dynamically. We do this by removing the existing viewport
     * element and adding a new one to work around bugs on some mobile devices.
     */
    _updateViewport: function ()
    {
        var viewportContent = document.documentElement.clientWidth <= 880 ?
            'width=880, user-scalable=no' : 'width=device-width';

        this._setViewport(viewportContent);
    },

    /** Update the viewport to the new viewport content
     *
     * We do this by appending a new viewport element for cross-browser compatibility.
     *
     * See:
     *
     *   https://miketaylr.com/posts/2014/02/dynamically-updating-meta-viewport.html
     *   https://miketaylr.com/posts/2015/08/dynamically-updating-meta-viewport-in-2015.html
     */
    _setViewport: function (viewportContent)
    {
        if (viewportContent !== this._viewportContent)
        {
            this._viewportContent = viewportContent;
            var meta = document.createElement('meta');
            meta.setAttribute('name', 'viewport');
            meta.setAttribute('content', viewportContent);
            document.head.appendChild(meta);
        }
    },

    onWindowResized: function ()
    {
        this._updateViewport();
    }
});

