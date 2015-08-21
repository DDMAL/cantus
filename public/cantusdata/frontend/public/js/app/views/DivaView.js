define(['marionette',
        'backbone',
        'jquery',
        "underscore",
        "diva",
        "diva/plugins/highlight",
        "diva/plugins/download",
        "diva/plugins/canvas",
        "diva/plugins/pagealias",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
function(Marionette,
         Backbone,
         $,
         _,
         diva,
         DivaHighlight,
         DivaDownload,
         DivaCanvas,
         DivaPagealias,
         GlobalEventHandler,
         GlobalVars)
{

"use strict";

/** Define the format we expect the Diva filenames to adhere to */
var DIVA_FILENAME_REGEX = (/^(.+)_(.*?)\.([^.]+)$/);

var manuscriptChannel = Backbone.Radio.channel('manuscript');

/**
 * Manages the lifecycle and customization of the Diva viewer
 */
return Marionette.ItemView.extend({
    template: "#diva-template",

    ui: {
        divaWrapper: "#diva-wrapper"
    },

    behaviors: {
        resize: {
            target: '.diva-outer',
            action: 'publishDivaPanelResizedEvent'
        }
    },

    initialize: function(options)
    {
        _.bindAll(this, 'propagateFolioChange', 'onViewerLoad', 'setFolio',
            'setGlobalFullScreen', 'zoomToLocation', 'getPageAlias',
            'gotoInputPage', 'getPageWhichMatchesAlias', 'onDocLoad');

        this._imagePrefix = null;
        this._imageSuffix = null;

        this.divaEventHandles = [];

        // Create a debounced function to alert Diva that its panel size
        // has changed
        this.publishDivaPanelResizedEvent = _.debounce(function ()
        {
            diva.Events.publish("PanelSizeDidChange");
        }, 500);

        this.toolbarParentObject = this.options.toolbarParentObject;

        // TODO(wabain): get this from the manuscript channel for consistency
        this.siglum = options.siglum;

        // Update the folio on change
        // FIXME(wabain): Support manuscript change?
        this.listenTo(manuscriptChannel, 'change:folio', function (number)
        {
            this.setFolio(number);
        });
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

        this._imagePrefix = null;
        this._imageSuffix = null;
    },

    /**
     * Initialize Diva and subscribe to its events.
     */
    initializeDiva: function()
    {
        var siglum = this.siglum;

        var options = {
            toolbarParentObject: this.toolbarParentObject,
            viewerWidthPadding: 0,

            enableAutoTitle: false,
            enableAutoWidth: false,
            enableAutoHeight: false,
            enableFilename: false,
            enableHighlight: true,
            enableDownload: true,

            enablePagealias: true,
            pageAliasFunction: this.getPageAlias,

            fixedHeightGrid: false,

            enableKeyScroll: false,
            enableSpaceScroll: false,
            enableCanvas: true,

            iipServerURL: GlobalVars.iipImageServerUrl,
            objectData: "/static/" + siglum + ".json",
            imageDir: GlobalVars.divaImageDirectory + siglum,

            blockMobileMove: false
        };

        // Destroy the diva div just in case
        this.ui.divaWrapper.empty();
        // Initialize Diva
        this.ui.divaWrapper.diva(options);

        // TODO(wabain): Take this out after upgrading to Diva 4.0
        // Remove the extra viewport element Diva inserts on mobile devices
        $(document.head).find('meta[name=viewport]').slice(1).remove();

        this.divaInstance = this.ui.divaWrapper.data('diva');

        this.onDivaEvent("ViewerDidLoad", this.onViewerLoad);
        this.onDivaEvent("VisiblePageDidChange", this.propagateFolioChange);
        this.onDivaEvent("ModeDidSwitch", this.setGlobalFullScreen);
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
            // jshint devel:true
            console.warn(
                "Trying to mitigate a Diva zooming bug...\n" +
                "If you're not using Chrome, you shouldn't be seeing this.\n" +
                "See https://github.com/DDMAL/cantus/issues/206");

            inner[0].style.width = (cssWidth + 1) + 'px';
        }
    },

    /**
     * Return an alias for display based on the folio for the page at the given index
     *
     * @param pageIndex
     * @returns {string}
     */
    getPageAlias: function (pageIndex)
    {
        var folio = this.imageNameToFolio(this.divaFilenames[pageIndex]);

        var pageNumber = pageIndex + 1;

        // Append an opening parenthesis and the page number
        // This is a hack, since Diva doesn't have functionality to customize the page label
        // beyond the pagealias plugin
        return folio + ' (' + pageNumber;
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

        var actualPage = this.getPageWhichMatchesAlias(pageAlias);

        if (actualPage === null)
        {
            alert("Invalid page number");
        }
        else
        {
            this.divaInstance.gotoPageByIndex(actualPage);
        }
    },

    /**
     * Implement lenient matching for a page alias. Handle leading zeros for
     * numerical folio names, prefix characters (for appendices, etc.) and suffix
     * characters (e.g. r and v for recto and verso).
     *
     * Given a bare page number, it will automatically match it with a recto page
     * with that number.
     *
     * Examples: Suppose the folios are named 0000a, 0000b, 001r, 001v, and A001r
     *
     *   - 0a would match 0000a
     *   - a1 would match A001r
     *   - 0001 would match 001r
     *
     * @param alias {string}
     * @returns {number|null} The index of the page with the matching folio name
     */
    getPageWhichMatchesAlias: function (alias)
    {
        if (!alias)
            return null;

        // Try to split the page alias into the following components:
        //   - an optional non-numerical leading value
        //   - an integer value (with leading zeros stripped)
        //   - an optional non-numerical trailing value
        var coreNumber = /^\s*([^0-9]*)0*([1-9][0-9]*|0)([^0-9]*)\s*$/.exec(alias);

        var aliasRegex;

        if (coreNumber)
        {
            var leading = coreNumber[1],
                number = coreNumber[2],
                trailing = coreNumber[3];

            leading = this.escapeRegex(leading);

            if (trailing)
            {
                trailing = this.escapeRegex(trailing);
            }
            else
            {
                // If there is no trailing value, then allow for a recto suffix by default
                trailing = 'r?';
            }

            // Get a case-insensitive regex which allows any number of leading zeros
            // and then the number
            aliasRegex = new RegExp('^' + leading + '0*' + number + trailing + '$', 'i');
        }
        else
        {
            // If the core number detection failed, just strip whitespace and get a case-insensitive regex
            aliasRegex = new RegExp('^' + this.escapeRegex(alias.replace(/(^\s+|\s+$)/g, '')) + '$', 'i');
        }

        // Find a folio which matches this pattern
        // TODO(wabain): cache folio names
        var length = this.divaFilenames.length;
        for (var i = 0; i < length; i++)
        {
            if (this.imageNameToFolio(this.divaFilenames[i]).match(aliasRegex))
            {
                return i;
            }
        }

        // We didn't find a match; fall back to treating this as a non-aliased page number
        if (alias.match(/^\d+$/))
        {
            var pageIndex = parseInt(alias, 10) - 1;

            if (pageIndex >= 0 && pageIndex < length)
            {
                return pageIndex;
            }
        }

        // If nothing worked, then just return null
        return null;
    },

    /**
     * Escape a string so that it can be used searched for literally in a regex.
     * Implementation adapted from Backbone.Router._routeToRegExp
     */
    escapeRegex: function (s)
    {
        return s.replace(/[\-{}\[\]+?.,\\\^$|#\s]/g, '\\$&');
    },

    onShow: function()
    {
        this.initializeDiva();
    },

    setGlobalFullScreen: function(isFullScreen)
    {
        if (isFullScreen)
        {
            GlobalEventHandler.trigger("divaFullScreen");
        }
        else
        {
            GlobalEventHandler.trigger("divaNotFullScreen");
            this.triggerMethod('recalculate:size');
        }
    },

    /**
     * Calculate the page size and store the index and filename of the first
     * loaded page.
     */
    onViewerLoad: function()
    {
        this.triggerMethod('recalculate:size');
        this.trigger('loaded:viewer');

        // Go to the predetermined initial folio if one is set
        var initialFolio = manuscriptChannel.request('folio');
        if (initialFolio !== null)
            this.setFolio(initialFolio);

        // Store the list of filenames
        this.divaFilenames = this.divaInstance.getFilenames();

        // Customize the toolbar
        this._customizeToolbar();
    },

    /** Do some awkward manual manipulation of the toolbar */
    _customizeToolbar: function()
    {
        // Rebind the go to page input
        var input = this.$(this.divaInstance.getInstanceSelector() + 'goto-page');

        input.off('submit');
        input.on('submit', this.gotoInputPage);

        // Rename the current page label from Page to Folio
        var pageLabel = this.toolbarParentObject.find('.diva-page-label')[0];
        pageLabel.firstChild.textContent = 'Folio ';

        // Add a closing parenthesis (the opening is within the page alias)
        pageLabel.appendChild(document.createTextNode(')'));

        // Hack: Make the go to page input a Bootstrap input group
        var inputGroup = $('<div class="input-group input-group-sm">');
        var inputGroupBtnContainer = $('<div class="input-group-btn">');

        this.toolbarParentObject.find('.diva-goto-form input[type=submit]')
            .addClass('btn btn-default')
            .appendTo(inputGroupBtnContainer);

        this.toolbarParentObject.find('.diva-goto-form .diva-input')
            .addClass('form-control')
            .replaceWith(inputGroup)
            .appendTo(inputGroup);

        inputGroup.append(inputGroupBtnContainer);
    },

    /**
     * Set the diva viewer to load a specific folio...
     *
     * @param folioCode
     */
    setFolio: function(folioCode)
    {
        if (!this.divaInstance)
            return;

        var newImageName = this.folioToImageName(folioCode);

        // Don't jump to the folio if we're already somewhere on it (this would just make Diva
        // jump to the top of the page)
        if (newImageName === this.divaInstance.getCurrentPageFilename())
            return;

        this.divaInstance.gotoPageByName(newImageName);
    },

    /**
     * Change the page-wide folio value
     *
     * @param {Number} index
     * @param {String} fileName
     */
    propagateFolioChange: function(index, fileName)
    {
        this.triggerFolioChange(this.imageNameToFolio(fileName));
    },

    triggerFolioChange: _.debounce(function (folio)
    {
        manuscriptChannel.request('set:folio', folio, {replaceState: true});
    }, 250),

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

        this.divaInstance.resetHighlights();

        // Grab the array of page filenames straight from Diva.
        var pageFilenameArray = this.divaInstance.getFilenames();

        // Use the Diva highlight plugin to draw the boxes
        var highlightsByPageHash = {};
        var pageList = [];

        for (var i = 0; i < boxSet.length; i++)
        {
            // Translate folio to Diva page
            var folioCode = boxSet[i].p;
            var pageFilename = this.folioToImageName(folioCode);
            var pageIndex = pageFilenameArray.indexOf(pageFilename);

            if (highlightsByPageHash[pageIndex] === undefined)
            {
                // Add page to the hash
                highlightsByPageHash[pageIndex] = [];
                pageList.push(pageIndex);
            }
            // Page is in the hash, so we add to it.
            highlightsByPageHash[pageIndex].push
            ({
                'width': boxSet[i].w,
                'height': boxSet[i].h,
                'ulx': boxSet[i].x,
                'uly': boxSet[i].y
            });
        }
        // Now we need to add all of the pages to the Diva viewer
        for (var j = 0; j < pageList.length; j++)
        {
            this.divaInstance.highlightOnPage
            (
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
        // Grab the diva internals to work with
        var divaData = this.divaInstance;

        // Do nothing if there's no box or if Diva is not initialized
        if (!box || !divaData)
            return;

        var divaSettings = divaData.getSettings();

        // Now figure out the page that box is on
        var divaOuter = divaSettings.outerObject;
        var zoomLevel = divaData.getZoomLevel();

        // Grab the array of page filenames straight from Diva.
        var pageFilenameArray = divaData.getFilenames();
        var folioCode = box.p;
        var pageFilename = this.folioToImageName(folioCode);
        var desiredPage = pageFilenameArray.indexOf(pageFilename) + 1;

        // Now jump to that page
        divaData.gotoPageByNumber(desiredPage);
        // Get the height above top for that box
        var boxTop = divaData.translateFromMaxZoomLevel(box.y);
        var currentScrollTop = parseInt(divaOuter.scrollTop(), 10);

        var topMarginConsiderations = divaSettings.averageHeights[zoomLevel] * divaSettings.adaptivePadding;
        var leftMarginConsiderations = divaSettings.averageWidths[zoomLevel] * divaSettings.adaptivePadding;

        divaOuter.scrollTop(boxTop + currentScrollTop - (divaOuter.height() / 2) + (box.h / 2) +
            topMarginConsiderations);

        // Now get the horizontal scroll
        var boxLeft = divaData.translateFromMaxZoomLevel(box.x);
        divaOuter.scrollLeft(boxLeft - (divaOuter.width() / 2) + (box.w / 2) + leftMarginConsiderations);
        // Will include the padding between pages for best results
    },

    /*
     * Helpers for filename/folio translation
     *
     * FIXME: We shouldn't need to translate between filenames and folios at all
     *
     * Maybe IIIF metadata can help with that?
     */

    /**
     * Takes an image file name and returns the folio code.
     *
     * @param imageName Some image name, ex: "folio_001.jpg"
     * @returns string "001"
     */
    imageNameToFolio: function(imageName)
    {
        return this._parseDivaFilename(imageName)[2];
    },

    /**
     * Return the image filename corresponding to a given folio number
     *
     * This function relies on the assumption that all images in a document
     * have the filename format, consisting of [siglum slug]_[folio number].[extension]
     *
     * @param {string} folioCode
     * @returns {string}
     */
    folioToImageName: function(folioCode)
    {
        // If we haven't yet stored the filename prefix and extension, do it now
        if (this._imagePrefix === null)
        {
            var filename = this.divaInstance.getFilenames()[0];
            var components = this._parseDivaFilename(filename);

            this._imagePrefix = components[1];
            this._imageSuffix = components[3];
        }

        return this._imagePrefix + '_' + folioCode + '.' + this._imageSuffix;
    },

    /**
     * Parse a given Diva image filename into its constituent parts, throwing
     * an error on failure
     * @param filename
     * @returns {Array}
     * @private
     */
    _parseDivaFilename: function(filename)
    {
        var components = DIVA_FILENAME_REGEX.exec(filename);

        if (!components)
            throw new Error('failed to parse Diva image filename "' + filename + '"');

        return components;
    }
});
});