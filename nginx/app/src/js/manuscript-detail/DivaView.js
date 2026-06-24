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
            'getPageWhichMatchesAlias', 'onDocLoad', 'showPageSuggestions',
            'onManifestLoad');

        // Create a debounced function to alert the site that Diva has
        // changed the folio
        this.triggerFolioChange = _.debounce(function (imageURI) {
            manuscriptChannel.request('set:imageURI', imageURI, { replaceState: true });
        }, 250);

        this.listenTo(manuscriptChannel, 'change:imageURI', this.setImageURI);
        this.listenTo(manuscriptChannel, 'folioLoaded', this.updatePageAlias);

        this.toolbarParentObject = this.options.toolbarParentObject;

        // TODO(wabain): get this from the manuscript channel for consistency
        this.manifestUrl = options.manifestUrl;
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
            manifestUrl: this.manifestUrl,
            toolbarParentObject: this.toolbarParentObject
        });
        // Initialize Diva. On the v7 backend initialize() is async (it lazily
        // loads OpenSeadragon and the v7 bundle), so surface a load failure
        // instead of leaving an unhandled rejection behind a blank viewer.
        Promise.resolve(this.divaAdapter.initialize()).catch(function (error) {
            console.error('Failed to initialize the Diva viewer', error); // eslint-disable-line no-console
        });

        manuscriptChannel.reply('diva', () => this.divaAdapter);

        this.divaAdapter.on("viewer:loaded", this.onViewerLoad);
        this.divaAdapter.on("viewer:loaded", this.propagateFolioChange);
        this.divaAdapter.on("page:changed", this.propagateFolioChange);
        this.divaAdapter.on("document:loaded", this.onDocLoad);
        this.divaAdapter.on("manifest:loaded", this.onManifestLoad);
    },

    /**
     * Workaround for a weird Chrome bug - sometimes setting the style on the
     * diva-inner element doesn't work. The CSS value is changed, but the width
     * of the element itself is not. Manually re-applying the change in the Developer
     * Console makes it work, so it doesn't seem to be a styling issue.
     *
     * When this happens, setting the width to a different but close value seems to work.
     */
    onDocLoad: function () {
        var inner = this.ui.divaWrapper.find('.diva-inner');
        // The v7 viewer has no .diva-inner element, so this v6-only fix is irrelevant.
        if (!inner.length)
            return;

        var cssWidth = parseInt(inner[0].style.width, 10);

        if (cssWidth && cssWidth !== inner.width()) {
            /* eslint-disable no-console */
            console.warn(
                "Trying to mitigate a Diva zooming bug...\n" +
                "If you're not using Chrome, you shouldn't be seeing this.\n" +
                "See https://github.com/DDMAL/cantus/issues/206");
            /* eslint-enable no-console */

            inner[0].style.width = (cssWidth + 1) + 'px';
        }
    },

    /**
     * Update Diva's page index to show the folio name
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
        manuscriptChannel.trigger('set:pageAlias', pageAlias);
        // The folio label span only exists in the v6 toolbar; on v7 the alias
        // will reach the right-panel tab via set:pageAlias above.
        if (this.folioNumberSpan)
            this.folioNumberSpan.textContent = pageAlias;
    },

    /**
     * Replacement callback for the Diva page input submission
     */
    gotoInputPage: function (event) {
        event.preventDefault();
        // If the form was explicitly submitted by the user (eg. by clicking "Go"
        // or pressing the Enter key), we take the first suggestion as the page
        // destination. If the form was triggered by the user clicking a page
        // suggestion, we take the clicked suggestion as the destination (this is already
        // set in the Diva default handler for a "mousedown" event).
        if (event.originalEvent) {
            var inputSuggestions = this.toolbarParentObject.find(this.divaAdapter.getInstanceSelector() + 'input-suggestions');
            var pageInput = $('.diva-input-suggestion:first', inputSuggestions);
            var pageAlias = pageInput.text();
        } else {
            var pageInput = $(this.divaAdapter.getInstanceSelector() + 'goto-page-input').get(0);
            var pageAlias = pageInput.value
        }

        if (!pageAlias)
            return;

        this.getPageWhichMatchesAlias(pageAlias).done(_.bind(function (page) {
            this.divaAdapter.gotoPageByURI(page);

        }, this)).fail(function () {
            alert("Invalid page number");
        });
    },
    /**
     * 
     * Replacement callback for the Diva page input search suggestions.
     * Suggestions are taken from folio numbers in solr/Django db rather
     * than the IIIF manifest.
     */

    showPageSuggestions: function showPageSuggestions(event) {
        var inputSuggestions = this.toolbarParentObject.find(this.divaAdapter.getInstanceSelector() + 'input-suggestions');
        var manuscript = manuscriptChannel.request('manuscript');

        var pageInput = this.toolbarParentObject.find(this.divaAdapter.getInstanceSelector() + 'goto-page-input');

        var queryUrl = '/folio-set/manuscript/' + manuscript + '/?q=' + pageInput.val();
        $.get(queryUrl,
            function (data) {
                inputSuggestions.empty();
                for (const queryResult of data) {
                    var newInputSuggestion = document.createElement('div');
                    newInputSuggestion.setAttribute('class', 'diva-input-suggestion');
                    newInputSuggestion.textContent = queryResult.number;
                    inputSuggestions.append(newInputSuggestion);
                }
            }
        )

        inputSuggestions.css('display', 'block');
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

        // Customize the toolbar
        this._customizeToolbar();

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

        // Change initial view to document view
        this.divaAdapter.changeView('document');
    },

    /**
     * Once the manifest is loaded, grab any attribution and rights information
     * contained in the manifest and update the DOM to display it.
     * NOTE: Diva contains a plug-in ("IIIFMetadata") that could theoretically
     * be used to collect and show this data, but it errors if this data is
     * improperly formatted in the IIIF, so we introduce this here to tolerate
     * these cases.
     * NOTE: At the moment, we only support the IIIF 2 API, since Diva only
     * supports that version.
     **/
    onManifestLoad: function (manifest) {
        var attribution = manifest.attribution;
        var logo = manifest.logo;
        if (typeof logo === "object") {
            var logo_url = logo['@id'];
        } else {
            var logo_url = logo;
        }
        var licence = manifest.license;
        this.imageAttributionMetadata = {
            imageAttribution: attribution,
            imageLogoUrl: logo_url,
            imageLicence: licence
        };
    },

    /** Do some awkward manual manipulation of the toolbar */
    _customizeToolbar: function () {
        // v7 owns its toolbar in Elm and exposes no instance selector to graft
        // onto; its Cantus chrome is re-homed outside the viewer in Stage 3j.
        if (!this.divaAdapter.getInstanceSelector())
            return;

        // Rebind the go to page input
        var input = this.toolbarParentObject.find(this.divaAdapter.getInstanceSelector() + 'goto-page');

        input.off('submit');
        input.on('submit', this.gotoInputPage);

        // Rebind the go to page input focus
        var pageSearch = this.toolbarParentObject.find(this.divaAdapter.getInstanceSelector() + 'goto-page-input');

        pageSearch.off('input focus');
        pageSearch.on('input focus', this.showPageSuggestions)

        // Rename the current page label from Page to Folio
        var pageLabel = this.toolbarParentObject.find('.diva-page-label')[0];
        pageLabel.firstChild.textContent = '';

        // Add an empty span to display the folio name
        this.folioNumberSpan = document.createElement('span');
        pageLabel.insertBefore(this.folioNumberSpan, pageLabel.firstChild.nextSibling);

        pageLabel.insertBefore($('<span>').text(' (')[0], this.folioNumberSpan.nextSibling);

        // Add a closing parenthesis (the opening is within the page alias)
        pageLabel.appendChild(document.createTextNode(')'));
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
