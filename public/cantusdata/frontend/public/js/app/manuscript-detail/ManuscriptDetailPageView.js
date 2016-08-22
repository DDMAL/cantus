import $ from 'jquery';
import _ from 'underscore';
import Radio from 'backbone.radio';
import Marionette from 'marionette';
import diva from 'diva';

import SearchView from "search/SearchView";
import ChantSearchProvider from "search/chant-search/ChantSearchProvider";
import OMRSearchProvider from "search/omr-search/OMRSearchProvider";

import SidenavView from 'ui/SidenavView';

import FolioView from "./folio/FolioView";
import DivaView from "./DivaView";
import ManuscriptInfoView from "./ManuscriptInfoView";
import NavFolioNumberView from './NavFolioNumberView';
import DivaFolioAdvancerView from './DivaFolioAdvancerView';

import template from './manuscript.template.html';

var manuscriptStateChannel = Radio.channel('manuscript');

/**
 * This page shows an individual manuscript.  You get a nice diva viewer
 * and you can look through the chant info.
 *
 * @type {*|void}
 */
export default Marionette.LayoutView.extend({
    template,

    behaviors: {
        fillViewportHeight: true
    },

    regions: {
        divaViewRegion: "#diva-column",
        folioViewRegion: "#folio",
        searchViewRegion: "#manuscript-search",
        navFolioRegion: '#manuscript-nav-folio-number',
        folioAdvancerRegion: '#manuscript-folio-advancer-container'
    },

    ui: {
        toolbarRow: '#toolbar-row',
        resizer: '#manuscript-data-container .resizer',
        divaColumn: "#diva-column",
        manuscriptDataColumn: '#manuscript-data-column'
    },

    events: {
        'mousedown @ui.resizer': 'startResizing',
    },

    initialize: function ()
    {
        this._viewportContent = null;
    },

    startResizing: function (event)
    {
        //Only resize if the resizer was left clicked
        if (event.button !== 0)
            return;

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

            //Prevent one of the two elements to have a width smaller than 5%
            newWidthPercentage = Math.max(newWidthPercentage, 5);
            newWidthPercentage = Math.min(newWidthPercentage, 95);

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

    _showInfoSidenav()
    {
        this._infoSidenav.show();
    },

    onRender: function()
    {
        this._configurePageLayout();

        // Initialize the Diva view
        var divaView = new DivaView({
            manifestUrl: this.model.get("manifest_url"),
            toolbarParentObject: this.ui.toolbarRow
        });

        // Create a "Manuscript Info" button in the Diva toolbar
        this.listenToOnce(divaView, 'loaded:viewer', function ()
        {
            var manuscriptInfo = $('<div>').attr('id', 'manuscript-info-target');
            var manuscriptInfoButton = $('<button>').addClass('btn btn-link btn-sm').text('Manuscript info');
            manuscriptInfoButton.appendTo(manuscriptInfo);

            $(manuscriptInfoButton).on('click', this._showInfoSidenav.bind(this));
            manuscriptInfo.appendTo(this.ui.toolbarRow.find('.diva-tools-right'));
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

        // Render the subviews
        this.folioViewRegion.show(new FolioView());
        this.searchViewRegion.show(searchView);
        this.navFolioRegion.show(new NavFolioNumberView());
        this.folioAdvancerRegion.show(new DivaFolioAdvancerView());

        // Attach the info sidenav
        this._infoSidenavParent = $('<div class="manuscript-info-sidenav-container"></div>');
        this._infoSidenavParent.appendTo(document.body);

        this._infoSidenav = new SidenavView({
            el: this._infoSidenavParent,
            content: () => new ManuscriptInfoView({model: this.model})
        });

        this._infoSidenav.render();

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

    onDestroy()
    {
        this._infoSidenav.destroy();
        this._infoSidenavParent.remove();
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

