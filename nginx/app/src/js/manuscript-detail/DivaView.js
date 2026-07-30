import Marionette from 'marionette';
import Radio from 'backbone.radio';
import $ from 'jquery';
import _ from "underscore";

import DivaAdapter from './DivaAdapter';

import GlobalVars from '../config/GlobalVars';

import template from './diva.template.html';

var manuscriptChannel = Radio.channel('manuscript');

/**
 * Manages the lifecycle and customization of the Diva viewer
 */
export default Marionette.View.extend({
    template,
    tagName: 'div',
    className: 'propagate-height',

    ui: {
        divaWrapper: '#diva-wrapper'
    },

    initialize: function (options) {
        _.bindAll(this, 'propagateFolioChange', 'onViewerLoad', 'setImageURI',
            'updatePageAlias', 'gotoInputPage',
            'getPageWhichMatchesAlias', 'showPageSuggestions',
            'gotoSuggestedFolio', 'onManifestLoad');

        // Create a debounced function to alert the site that Diva has
        // changed the folio
        this.triggerFolioChange = _.debounce(function (imageURI) {
            manuscriptChannel.request('set:imageURI', imageURI, { replaceState: true });
        }, 250);

        this.listenTo(manuscriptChannel, 'change:imageURI', this.setImageURI);
        this.listenTo(manuscriptChannel, 'folioLoaded', this.updatePageAlias);

        this.toolbarParentObject = this.options.toolbarParentObject;
        this._bindFolioNavigation();

        // TODO(wabain): get this from the manuscript channel for consistency
        this.manifestUrl = options.manifestUrl;
    },

    /**
     * Bind the folio label and the goto-folio form in the Cantus toolbar row.
     * They are rendered by the parent view's template, outside this view's own
     * element, so they exist before the viewer loads and are independent of
     * the Diva backend in use.
     */
    _bindFolioNavigation: function () {
        this.folioLabelSpan = this.toolbarParentObject.find('#current-folio-label')[0];
        this.gotoFolioInput = this.toolbarParentObject.find('#goto-folio-input');
        this.gotoFolioSuggestions = this.toolbarParentObject.find('#goto-folio-suggestions');

        this.toolbarParentObject.find('#goto-folio-form').on('submit', this.gotoInputPage);
        this.gotoFolioInput.on('input focus', this.showPageSuggestions);
        // A clicked suggestion still navigates before this hides the list,
        // because its mousedown handler runs before the input loses focus.
        this.gotoFolioInput.on('blur', () => this.gotoFolioSuggestions.hide());
        this.gotoFolioSuggestions.on('mousedown', '.goto-folio-suggestion', this.gotoSuggestedFolio);
    },

    onBeforeDestroy: function () {
        // Uninitialize the Diva viewer, if it exists
        if (this.divaAdapter) {
            // Tear down the viewer and unsubscribe the event handlers
            this.divaAdapter.destroy();
            this.divaAdapter = null;
            manuscriptChannel.stopReplying('diva');
        }
    },

    /**
     * Initialize Diva and subscribe to its events.
     */
    initializeDiva: function () {
        // Destroy the diva div just in case
        this.ui.divaWrapper.empty();
        // Create the Diva adapter
        this.divaAdapter = new DivaAdapter({
            rootElementId: 'diva-wrapper',
            manifestUrl: this.manifestUrl
        });
        // initialize() is async (it lazily loads OpenSeadragon and the Diva
        // bundle), so surface a load failure instead of leaving an unhandled
        // rejection behind a blank viewer.
        Promise.resolve(this.divaAdapter.initialize()).catch(function (error) {
            console.error('Failed to initialize the Diva viewer', error); // eslint-disable-line no-console
        });

        manuscriptChannel.reply('diva', () => this.divaAdapter);

        this.divaAdapter.on("viewer:loaded", this.onViewerLoad);
        this.divaAdapter.on("viewer:loaded", this.propagateFolioChange);
        this.divaAdapter.on("page:changed", this.propagateFolioChange);
        this.divaAdapter.on("manifest:loaded", this.onManifestLoad);
    },

    /**
     * Update the folio label in the Cantus toolbar row, e.g. "Folio 006v (3 of 500)"
     */
    updatePageAlias: function () {
        let folioNumber = manuscriptChannel.request('folio');
        if (folioNumber != null) {
            if (_.isArray(folioNumber)) {
                folioNumber = folioNumber.join(', ');
            }
            var pageAlias = 'Folio ' + folioNumber;
        } else {
            let imageIndex = this.divaAdapter.getCurrentPageIndex() + 1;
            var pageAlias = 'Image ' + imageIndex;
        }

        var pagePosition = (this.divaAdapter.getCurrentPageIndex() + 1) + ' of ' + this.divaAdapter.getAllPageURIs().length;
        this.folioLabelSpan.textContent = pageAlias + ' (' + pagePosition + ')';
    },

    /**
     * Handle a goto-folio form submission. The first suggestion is taken as
     * the destination, falling back to the typed value when there is none.
     */
    gotoInputPage: function (event) {
        event.preventDefault();

        var firstSuggestion = this.gotoFolioSuggestions.children().first().text();
        this.gotoFolioSuggestions.hide();

        this._gotoFolioAlias(firstSuggestion || this.gotoFolioInput.val());
    },

    /**
     * Navigate to a clicked page suggestion. Bound to mousedown so it runs
     * before the input's blur hides the suggestion list.
     */
    gotoSuggestedFolio: function (event) {
        var pageAlias = event.currentTarget.textContent;

        this.gotoFolioInput.val(pageAlias);
        this.gotoFolioSuggestions.hide();

        this._gotoFolioAlias(pageAlias);
    },

    /**
     * Jump the viewer to the folio with the given alias, alerting the user if
     * it does not resolve to a page.
     */
    _gotoFolioAlias: function (pageAlias) {
        if (!pageAlias)
            return;

        this.getPageWhichMatchesAlias(pageAlias).done(_.bind(function (page) {
            this.divaAdapter.gotoPageByURI(page);
        }, this)).fail(function () {
            alert("Invalid page number");
        });
    },

    /**
     * Show suggestions under the goto-folio input while the user is typing.
     * Suggestions are taken from folio numbers in solr/Django db rather
     * than the IIIF manifest.
     */
    showPageSuggestions: function () {
        var manuscript = manuscriptChannel.request('manuscript');
        // The endpoint matches folio numbers with their leading zeros stripped
        // (e.g. "83r" for folio "083r"), so strip any the user typed as well,
        // making "83r", "083r" and "0083r" all suggest folio 083r.
        var query = this.gotoFolioInput.val().replace(/^0+/, '');
        var queryUrl = '/folio-set/manuscript/' + manuscript + '/?q=' + query;

        $.get(queryUrl, (data) => {
            this.gotoFolioSuggestions.empty();
            for (const queryResult of data) {
                var suggestion = document.createElement('div');
                suggestion.setAttribute('class', 'goto-folio-suggestion');
                suggestion.textContent = queryResult.number;
                this.gotoFolioSuggestions.append(suggestion);
            }
            this.gotoFolioSuggestions.show();
        });
    },
    /**
     * Query Solr to convert a folio name to an image URI
     *
     * @param alias {string} A folio name or page index
     * @returns {object} A promise that the image URI will be retrieved from Solr
     */
    getPageWhichMatchesAlias: function (alias) {
        var deferred = $.Deferred();

        if (!alias)
            return deferred.reject(null);

        var manuscript = manuscriptChannel.request('manuscript');
        $.ajax({
            url: GlobalVars.siteUrl + 'folios/?number=' + alias + '&manuscript=' + manuscript,
            success: function (response) {
                // jscs:disable requireDotNotation
                deferred.resolve(response[0]['image_uri']);
                // jscs:enable requireDotNotation
            },
            error: _.bind(function (response) {
                // We didn't find a match; fall back to treating this as a non-aliased page number
                if (alias.match(/^Image (\d+)$/)) {
                    var pageIndex = parseInt(alias.match(/^Image (\d+)$/)[1], 10) - 1;
                } else if (alias.match(/^\d+$/)) {
                    var pageIndex = parseInt(alias, 10) - 1;
                }
                if (pageIndex >= 0 && pageIndex < this.divaFilenames.length) {
                    return deferred.resolve(this.divaFilenames[pageIndex]);
                } else {
                    // If nothing worked, then just return null
                    return deferred.reject(response);
                }
            }, this)
        });

        return deferred.promise();
    },

    onAttach: function () {
        this.initializeDiva();
    },

    /**
     * Calculate the page size and store the index and filename of the first
     * loaded page.
     */
    onViewerLoad: function () {
        this.trigger('loaded:viewer');

        // Go to the predetermined initial folio if one is set
        var initialFolio = manuscriptChannel.request('folio') ? manuscriptChannel.request('folio') : manuscriptChannel.request('pageAlias');
        if (initialFolio !== null) {
            this.getPageWhichMatchesAlias(initialFolio).done(_.bind(function (initialImageURI) {
                this.setImageURI(initialImageURI);
                this.updatePageAlias(initialFolio);
            }, this));
        }
        else {
            // If one is not set, then set the global folio to the Diva viewer's initial page
            var imageURI = this.divaAdapter.getCurrentPageURI();
            manuscriptChannel.request('set:imageURI', imageURI, { replaceState: true });
        }

        // Store the list of filenames
        this.divaFilenames = this.divaAdapter.getAllPageURIs();
    },

    /**
     * Store the image attribution metadata the adapter extracted from the IIIF
     * manifest (already flattened to { imageAttribution, imageLogoUrl,
     * imageLicence }) and announce it so the page can wire it into the model.
     */
    onManifestLoad: function (metadata) {
        this.imageAttributionMetadata = metadata;
        this.trigger('loaded:manifest');
    },

    /**
     * Set the diva viewer to load a specific folio, based on the image URI
     *
     * @param imageURI
     */
    setImageURI: function (imageURI) {
        if (!this.divaAdapter)
            return;

        // Don't jump to the folio if we're already somewhere on it (this would just make Diva
        // jump to the top of the page)
        if (imageURI === this.divaAdapter.getCurrentPageURI())
            return;

        this.divaAdapter.gotoPageByURI(imageURI);
    },

    /**
     * Change the page-wide folio value
     *
     * @param page the normalized { index, imageURI } from 'page:changed'
     */
    propagateFolioChange: function (page) {
        // When triggered by the 'viewer:loaded' event there is no page payload,
        // so fall back to the URI of the document's current page.
        var imageURI = (page && page.imageURI) ? page.imageURI : this.divaAdapter.getCurrentPageURI();

        this.triggerFolioChange(imageURI);
    }
});
