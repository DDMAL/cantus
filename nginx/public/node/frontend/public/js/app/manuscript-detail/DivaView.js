import Marionette from 'marionette';
import Backbone from 'backbone';
import $ from 'jquery';
import _ from "underscore";

import diva from "diva";

import GlobalVars from '../config/GlobalVars';

import template from './diva.template.html';

var manuscriptChannel = Backbone.Radio.channel('manuscript');

/**
 * Manages the lifecycle and customization of the Diva viewer
 */
export default Marionette.ItemView.extend({
    template,
    tagName: 'div class="propagate-height"',

    ui: {
        divaWrapper: '#diva-wrapper'
    },

    initialize: function(options)
    {
        _.bindAll(this, 'propagateFolioChange', 'onViewerLoad', 'setImageURI',
            'paintBoxes', 'updatePageAlias', 'gotoInputPage',
            'getPageWhichMatchesAlias', 'onDocLoad', 'showPageSuggestions');

        this.divaEventHandles = [];

        // Create a debounced function to alert the site that Diva has
        // changed the folio
        this.triggerFolioChange = _.debounce(function (imageURI)
        {
            manuscriptChannel.request('set:imageURI', imageURI, {replaceState: true});
        }, 250);

        this.listenTo(manuscriptChannel, 'change:imageURI', this.setImageURI);
        this.listenTo(manuscriptChannel, 'change:folio', this.updatePageAlias);

        this.toolbarParentObject = this.options.toolbarParentObject;

        // TODO(wabain): get this from the manuscript channel for consistency
        this.manifestUrl = options.manifestUrl;
    },

    onBeforeDestroy: function()
    {
        // Uninitialize the Diva viewer, if it exists
        if (this.divaInstance)
        {
            // Call Diva's destructor
            this.divaInstance.destroy();
            this.divaInstance = null;

            // Unsubscribe the event handlers
            _.forEach(this.divaEventHandles, function (handle)
            {
                diva.Events.unsubscribe(handle);
            });

            this.divaEventHandles.splice(this.divaEventHandles.length);
        }
    },

    /**
     * Initialize Diva and subscribe to its events.
     */
    initializeDiva: function()
    {
        var manifestUrl = this.manifestUrl;

        var options = {
            toolbarParentObject: this.toolbarParentObject,
            viewerWidthPadding: 0,

            enableAutoTitle: false,
            enableAutoWidth: false,
            enableAutoHeight: false,
            enableFilename: false,
            enableImageTitles: false,

            enableHighlight: true,
            enableDownload: true,

            fixedHeightGrid: true,

            enableKeyScroll: false,
            enableSpaceScroll: false,
            enableCanvas: true,

            objectData: '/manifest-proxy/' + manifestUrl,

            blockMobileMove: false
        };

        // Destroy the diva div just in case
        this.ui.divaWrapper.empty();
        // Initialize Diva
        this.ui.divaWrapper.diva(options);

        this.divaInstance = this.ui.divaWrapper.data('diva');

        this.onDivaEvent("ViewerDidLoad", this.onViewerLoad);
        this.onDivaEvent("ViewerDidLoad", this.propagateFolioChange);
        this.onDivaEvent("VisiblePageDidChange", this.propagateFolioChange);
        this.onDivaEvent("DocumentDidLoad", this.onDocLoad);
    },

    /**
     * Subscribe to a Diva event, registering it for automatic deregistration
     * @param event
     * @param callback
     */
    onDivaEvent: function (event, callback)
    {
        this.divaEventHandles.push(diva.Events.subscribe(event, callback));
    },

    /**
     * Workaround for a weird Chrome bug - sometimes setting the style on the
     * diva-inner element doesn't work. The CSS value is changed, but the width
     * of the element itself is not. Manually re-applying the change in the Developer
     * Console makes it work, so it doesn't seem to be a styling issue.
     *
     * When this happens, setting the width to a different but close value seems to work.
     */
    onDocLoad: function ()
    {
        var inner = this.ui.divaWrapper.find('.diva-inner');
        var cssWidth = parseInt(inner[0].style.width, 10);

        if (cssWidth && cssWidth !== inner.width())
        {
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
     *
     * @param folioName
     */
    updatePageAlias: function (folioName)
    {
        const stringFolioName = new String(folioName);
        const spacedFolioName = stringFolioName.split(",").join(", ");
        this.folioNumberSpan.textContent = folioName;
    },

    /**
     * Replacement callback for the Diva page input submission
     */
    gotoInputPage: function (event)
    {
        event.preventDefault();

        var pageInput = this.toolbarParentObject.find(this.divaInstance.getInstanceSelector() + 'goto-page-input');
        var pageAlias = pageInput.val();

        if (!pageAlias)
            return;

        this.getPageWhichMatchesAlias(pageAlias).done(_.bind(function (page)
        {
            this.divaInstance.gotoPageByName(page);

        }, this)).fail(function ()
        {
            alert("Invalid page number");
        });
    },
    /**
     * 
     * Replacement callback for the Diva page input search suggestions.
     * Suggestions are taken from folio numbers in solr/Django db rather
     * than the IIIF manifest.
     */

    showPageSuggestions: function showPageSuggestions(event){
        var inputSuggestions = this.toolbarParentObject.find(this.divaInstance.getInstanceSelector() + 'input-suggestions');
        var manuscript = manuscriptChannel.request('manuscript');

        var pageInput = this.toolbarParentObject.find(this.divaInstance.getInstanceSelector() + 'goto-page-input');

        var queryUrl =  '/folio-set/manuscript/' + manuscript + '/?q=' + pageInput.val();
        $.get(queryUrl,
            function (data){
                inputSuggestions.empty();
                for (const queryResult of data){
                    var newInputSuggestion = document.createElement('div');
                    newInputSuggestion.setAttribute('class','diva-input-suggestion');
                    newInputSuggestion.textContent = queryResult.number;
                    inputSuggestions.append(newInputSuggestion);
                }
            }
        )

        inputSuggestions.css('display','block');
    },
    /**
     * Query Solr to convert a folio name to an image URI
     *
     * @param alias {string} A folio name or page index
     * @returns {object} A promise that the image URI will be retrieved from Solr
     */
    getPageWhichMatchesAlias: function (alias)
    {
        var deferred = $.Deferred();

        if (!alias)
            return deferred.reject(null);

        var manuscript = manuscriptChannel.request('manuscript');
        $.ajax({
            url: GlobalVars.siteUrl + 'folios/?number=' + alias + '&manuscript=' + manuscript,
            success: function (response)
            {
                // jscs:disable requireDotNotation
                deferred.resolve(response[0]['image_uri']);
                // jscs:enable requireDotNotation
            },
            error: _.bind(function(response)
            {
                // We didn't find a match; fall back to treating this as a non-aliased page number
                if (alias.match(/^\d+$/))
                {
                    var pageIndex = parseInt(alias, 10) - 1;

                    if (pageIndex >= 0 && pageIndex < this.divaFilenames.length)
                    {
                        return deferred.resolve(this.divaFilenames[pageIndex]);
                    }
                }

                // If nothing worked, then just return null
                return deferred.reject(response);
            }, this)
        });

        return deferred.promise();
    },

    onShow: function()
    {
        this.initializeDiva();
    },

    /**
     * Calculate the page size and store the index and filename of the first
     * loaded page.
     */
    onViewerLoad: function()
    {
        this.trigger('loaded:viewer');

        // Go to the predetermined initial folio if one is set
        var initialFolio = manuscriptChannel.request('folio');
        if (initialFolio !== null)
        {
            this.getPageWhichMatchesAlias(initialFolio).done(_.bind(function (initialImageURI)
            {
                this.setImageURI(initialImageURI);
                this.updatePageAlias(initialFolio);
            }, this));
        }
        else
        {
            // If one is not set, then set the global folio to the Diva viewer's initial page
            var imageURI = this.divaInstance.getCurrentPageFilename();
            manuscriptChannel.request('set:imageURI', imageURI, {replaceState: true});
        }

        // Store the list of filenames
        this.divaFilenames = this.divaInstance.getFilenames();

        // Customize the toolbar
        this._customizeToolbar();

        // Change initial view to document view
        this.divaInstance.changeView('document');
    },

    /** Do some awkward manual manipulation of the toolbar */
    _customizeToolbar: function()
    {
        // Rebind the go to page input
        var input = this.toolbarParentObject.find(this.divaInstance.getInstanceSelector() + 'goto-page');

        input.off('submit');
        input.on('submit', this.gotoInputPage);

        // Rebind the go to page input focus
        var pageSearch = this.toolbarParentObject.find(this.divaInstance.getInstanceSelector() + 'goto-page-input');

        pageSearch.off('input focus');
        pageSearch.on('input focus', this.showPageSuggestions)

        // Rename the current page label from Page to Folio
        var pageLabel = this.toolbarParentObject.find('.diva-page-label')[0];
        pageLabel.firstChild.textContent = 'Folio ';

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
    setImageURI: function(imageURI)
    {
        if (!this.divaInstance)
            return;

        // Don't jump to the folio if we're already somewhere on it (this would just make Diva
        // jump to the top of the page)
        if (imageURI === this.divaInstance.getCurrentPageFilename())
            return;

        this.divaInstance.gotoPageByName(imageURI);
    },

    /**
     * Change the page-wide folio value
     *
     * @param {Number} index
     * @param {String} fileName
     */
    propagateFolioChange: function(_, imageURI)
    {
        // In the case that this is triggered by the 'ViewerDidLoad' event,
        // Set the imageURI to be URI of the first page of the document
        if (!imageURI)
            imageURI = this.divaInstance.getCurrentPageFilename();

        this.triggerFolioChange(imageURI);
    },

    /**
     * Draw boxes on the Diva viewer.  These usually correspond to
     * music notation on a manuscript page.
     * music notation on a manuscript page.
     *
     * @param boxSet [ {p,w,h,x,y}, ... ]
     */
    paintBoxes: function(boxSet)
    {
        if (!this.divaInstance)
            return;

        // Wait for the Diva instance to be ready
        if (!this.divaInstance.isReady())
        {
            this.divaEventHandles.push(diva.Events.subscribe("ViewerDidLoad", function ()
            {
                this.paintBoxes(boxSet);
            }.bind(this)));
            return;
        }

        this.divaInstance.resetHighlights();

        // Use the Diva highlight plugin to draw the boxes
        var highlightsByPageHash = {};
        var pageList = [];

        for (var i = 0; i < boxSet.length; i++)
        {
            // Translate folio to Diva page
            var pageFilename = boxSet[i].p;
            var pageIndex = this.divaFilenames.indexOf(pageFilename);

            if (highlightsByPageHash[pageIndex] === undefined)
            {
                // Add page to the hash
                highlightsByPageHash[pageIndex] = [];
                pageList.push(pageIndex);
            }
            // Page is in the hash, so we add to it.
            highlightsByPageHash[pageIndex].push({
                'width': boxSet[i].w,
                'height': boxSet[i].h,
                'ulx': boxSet[i].x,
                'uly': boxSet[i].y
            });
        }
        // Now we need to add all of the pages to the Diva viewer
        for (var j = 0; j < pageList.length; j++)
        {
            this.divaInstance.highlightOnPage(
                pageList[j], // The page number
                highlightsByPageHash[pageList[j]] // List of boxes
            );
        }
    },

    /**
      * Zoom Diva to a location.
      *
      * @param box
      */
    zoomToLocation: function(box)
    {
        if (!this.divaInstance)
            return;

        // Wait for the Diva instance to be ready
        if (!this.divaInstance.isReady())
        {
            this.divaEventHandles.push(diva.Events.subscribe("ViewerDidLoad", function ()
            {
                this.zoomToLocation(box);
            }.bind(this)));
            return;
        }

        // Grab the diva internals to work with
        var divaData = this.divaInstance;

        // Do nothing if there's no box or if Diva is not initialized
        if (!box || !divaData)
        return;

        var divaSettings = divaData.getSettings();
        // Now figure out the page that box is on
        var divaOuter = divaSettings.outerObject;

        var pageFilename = box.p;
        var desiredPage = this.divaFilenames.indexOf(pageFilename);

        // Now jump to that page
        divaData.gotoPageByIndex(desiredPage);
        // Get the height above top for that box
        var boxTop = divaData.translateFromMaxZoomLevel(box.y);
        var currentScrollTop = parseInt(divaOuter.scrollTop(), 10);

        // TODO, find workaround since Diva 5 dropped 'averageHeights' and 'averageWidths'
        // var zoomLevel = divaData.getZoomLevel();
        var topMarginConsiderations = 0; // = divaSettings.averageHeights[zoomLevel] * divaSettings.adaptivePadding;
        var leftMarginConsiderations = 0; // = divaSettings.averageWidths[zoomLevel] * divaSettings.adaptivePadding;

        divaOuter.scrollTop(boxTop + currentScrollTop - (divaOuter.height() / 2) + (box.h / 2) +
               topMarginConsiderations);

        // Now get the horizontal scroll
        var boxLeft = divaData.translateFromMaxZoomLevel(box.x);
        divaOuter.scrollLeft(boxLeft - (divaOuter.width() / 2) + (box.w / 2) + leftMarginConsiderations);
        // Will include the padding between pages for best results
    }
});
