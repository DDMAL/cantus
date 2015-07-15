define(['marionette', 'jquery',
        "underscore",
        "diva",
        "diva-highlight",
        "diva-download",
        "diva-canvas",
        "diva-pagealias",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
function(Marionette, $,
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

/**
 * Provide an alert message to the user.
 */
return Marionette.ItemView.extend
({
    //el: "#diva-wrapper",

    /**
     * The tag wrapping the diva stuff
     */
    tagName: 'div class="row"',
    template: "#diva-template",

    divaInitialized: false,

    // Only used if initial folio
    initialFolio: undefined,

    currentFolioIndex: -1,
    currentFolioName: 0,

    imagePrefix: null,
    imageSuffix: "",

    ui: {
        divaToolbar: "#diva-toolbar",
        divaWrapper: "#diva-wrapper"
    },

    // Diva Event handlers
    viewerLoadEvent: null,
    pageAliasingInitEvent: null,
    pageChangeEvent: null,
    modeSwitchEvent: null,
    docLoadEvent: null,

    behaviors: {
        resize: {
            target: '.diva-outer',
            action: 'publishDivaPanelResizedEvent'
        }
    },

    initialize: function(options)
    {
        _.bindAll(this, 'storeFolioIndex', 'onViewerLoad', 'setFolio',
            'setGlobalFullScreen', 'zoomToLocation', 'getPageAlias',
            'initializePageAliasing', 'gotoInputPage', 'getPageWhichMatchesAlias',
            'onDocLoad');

        // Create a debounced function to alert Diva that its panel size
        // has changed
        this.publishDivaPanelResizedEvent = _.debounce(function ()
        {
            diva.Events.publish("PanelSizeDidChange");
        }, 500);

        //this.el = options.el;
        this.setManuscript(options.siglum, options.folio);
    },

    onBeforeDestroy: function()
    {
        // Uninitialize Diva
        this.uninitializeDiva();
        // Clear the fields
        this.initialFolio = null;
        this.currentFolioName = null;
        this.currentFolioIndex = null;
        this.imagePrefix = null;
        this.imageSuffix = null;
        this.viewerLoadEvent = null;
        this.pageAliasingInitEvent = null;
        this.modeSwitchEvent = null;
    },

    /**
     * Destroy the Diva viewer, if it exists.
     */
    uninitializeDiva: function()
    {
        // Diva's default destructor
        this.getDivaData().destroy();

        if (this.divaInitialized)
        {
            // Unsubscribe the event handlers
            if (this.viewerLoadEvent !== null)
            {
                diva.Events.unsubscribe(this.viewerLoadEvent);
            }
            if (this.pageAliasingInitEvent !== null)
            {
                diva.Events.unsubscribe(this.pageAliasingInitEvent);
            }
            if (this.pageChangeEvent !== null)
            {
                diva.Events.unsubscribe(this.pageChangeEvent);
            }
            if (this.modeSwitchEvent !== null)
            {
                diva.Events.unsubscribe(this.modeSwitchEvent);
            }
            if (this.docLoadEvent !== null)
            {
                diva.Events.unsubscribe(this.docLoadEvent);
            }
        }
    },

    /**
     * Initialize Diva and subscribe to its events.
     */
    initializeDiva: function()
    {
        var siglum = this.siglum;

        var options = {
            toolbarParentObject: this.ui.divaToolbar,
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

            iipServerURL: GlobalVars.iipImageServerUrl + "fcgi-bin/iipsrv.fcgi",
            objectData: "/static/" + siglum + ".json",
            imageDir: GlobalVars.divaImageDirectory + siglum
        };

        // Destroy the diva div just in case
        this.ui.divaWrapper.empty();
        // Initialize Diva
        this.ui.divaWrapper.diva(options);

        this.viewerLoadEvent = diva.Events.subscribe("ViewerDidLoad", this.onViewerLoad);
        this.pageAliasingInitEvent = diva.Events.subscribe("ViewerDidLoad", this.initializePageAliasing);
        this.pageChangeEvent = diva.Events.subscribe("VisiblePageDidChange", this.storeFolioIndex);
        this.modeSwitchEvent = diva.Events.subscribe("ModeDidSwitch", this.setGlobalFullScreen);

        this.docLoadEvent = diva.Events.subscribe("DocumentDidLoad", this.onDocLoad);

        // Remember that we've initialized diva
        this.divaInitialized = true;
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

        var pageAlias = $(this.ui.divaToolbar.find(this.getDivaData().getInstanceSelector() + 'goto-page-input')).val();

        if (!pageAlias)
            return;

        var actualPage = this.getPageWhichMatchesAlias(pageAlias);

        if (actualPage === null)
        {
            alert("Invalid page number");
        }
        else
        {
            this.getDivaData().gotoPageByIndex(actualPage);
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
        GlobalEventHandler.trigger("renderView");
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
     * Set the manuscript.
     *
     * @param siglum
     * @param initialFolio
     */
    setManuscript: function(siglum, initialFolio)
    {
        this.siglum = String(siglum);
        if (initialFolio !== undefined)
        {
            this.initialFolio = String(initialFolio);
        }
    },

    /**
     * Calculate the page size and store the index and filename of the first
     * loaded page.
     */
    onViewerLoad: function()
    {
        this.triggerMethod('recalculate:size');

        // If there exists a client-defined initial folio
        if (this.initialFolio !== undefined)
        {
            this.setFolio(this.initialFolio);
        }
        // Grab data from diva
        var divaData = this.getDivaData();
        // Store the initial folio
        //debugger;
        var number = divaData.getCurrentPageIndex();
        var name = divaData.getCurrentPageFilename();
        this.storeFolioIndex(number, name);
        // Store the image prefix for later
        this.setImagePrefixAndSuffix(name);
    },

    initializePageAliasing: function()
    {
        var divaData = this.getDivaData();

        // Store the list of filenames
        this.divaFilenames = divaData.getFilenames();

        // Rebind the page input
        var input = this.$(divaData.getInstanceSelector() + 'goto-page');

        // Remove the original binding
        input.off('submit');

        // Add the replacement binding
        input.on('submit', this.gotoInputPage);

        // Rename the page label
        var pageLabel = this.ui.divaToolbar.find('.diva-page-label')[0];

        // Replace "Page " with "Folio "
        pageLabel.firstChild.textContent = 'Folio ';

        // Add a closing parenthesis (the opening is within the page alias)
        pageLabel.appendChild(document.createTextNode(')'));
    },

    /**
     * Sets this.imagePrefix from any image name.
     *
     * @param imageName
     */
    setImagePrefixAndSuffix: function(imageName)
    {
        // Suffix is usually just ".jpeg" or whatever...
        this.imageSuffix = String(imageName).split('.')[1];
        // Prefix is trickier
        var splitFolioName = String(imageName).split('.')[0].split('_');

        // Assemble the parts into an image prefix
        var prefix = "";
        for (var i = 0; i < (splitFolioName.length - 1); i++)
        {
            prefix += splitFolioName[i];
        }

        this.imagePrefix = prefix;
    },

    /**
     * Set the diva viewer to load a specific folio...
     *
     * @param folioCode
     */
    setFolio: function(folioCode)
    {
        // We might need to set the prefix and suffix
        if (this.imagePrefix === null || this.imageSuffix === "")
        {
            this.setImagePrefixAndSuffix(this.currentFolioName);
        }
        var newImageName = this.imagePrefix + "_" + String(folioCode) + "." + this.imageSuffix;
        if (this.getDivaData() !== undefined)
        {
            this.getDivaData().gotoPageByName(newImageName);
        }
    },

    getFolio: function()
    {
        return this.imageNameToFolio(this.currentFolioName);
    },

    /**
     * Store a folio index and image filename.
     *
     * @param index int
     * @param fileName string
     */
    storeFolioIndex: function(index, fileName)
    {
        // The first time it's ever called
        if (this.initialFolio === undefined)
        {
            this.initialFolio = 0;
        }
        // Not the first time
        else if (index !== this.currentFolioIndex)
        {
            this.currentFolioIndex = index;
            this.currentFolioName = fileName;
            this.triggerFolioChange(this.imageNameToFolio(fileName));
        }
    },

    triggerFolioChange: _.debounce(function (folio)
    {
        GlobalEventHandler.trigger("ChangeFolio", folio, {replaceState: true});
    }, 250),

    /**
     * Get the stored Diva data.
     *
     * @returns {*|jQuery}
     */
    getDivaData: function()
    {
        return this.ui.divaWrapper.data('diva');
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
        var divaData = this.getDivaData();

        divaData.resetHighlights();

        // Grab the array of page filenames straight from Diva.
        var pageFilenameArray = divaData.getFilenames();

        // We might have to manually reset the page prefix
        if (this.imagePrefix === null)
        {
            this.setImagePrefixAndSuffix(pageFilenameArray[0]);
        }

        // Use the Diva highlight plugin to draw the boxes
        var highlightsByPageHash = {};
        var pageList = [];

        for (var i = 0; i < boxSet.length; i++)
        {
            // Translate folio to Diva page
            var folioCode = boxSet[i].p;
            var pageFilename = this.imagePrefix + "_" + folioCode + ".jp2";
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
            divaData.highlightOnPage
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
        if (box === undefined)
        {
            // Do nothing if no box!
            return;
        }

        // Grab the diva internals to work with
        var divaData = this.getDivaData();

        // Now figure out the page that box is on
        var divaOuter = divaData.getSettings().outerObject;
        var zoomLevel = divaData.getZoomLevel();

        // Grab the array of page filenames straight from Diva.
        var pageFilenameArray = divaData.getFilenames();
        var folioCode = box.p;
        var pageFilename = this.imagePrefix + "_" + folioCode + ".jp2";
        var desiredPage = pageFilenameArray.indexOf(pageFilename) + 1;

        // Now jump to that page
        divaData.gotoPageByNumber(desiredPage);
        // Get the height above top for that box
        var boxTop = divaData.translateFromMaxZoomLevel(box.y);
        var currentScrollTop = parseInt(divaOuter.scrollTop(), 10);

        var topMarginConsiderations = divaData.getSettings().averageHeights[zoomLevel] *
            divaData.getSettings().adaptivePadding;
        var leftMarginConsiderations = divaData.getSettings().averageWidths[zoomLevel] *
            divaData.getSettings().adaptivePadding;

        divaOuter.scrollTop(boxTop + currentScrollTop - (divaOuter.height() / 2) + (box.h / 2) +
            topMarginConsiderations);

        // Now get the horizontal scroll
        var boxLeft = divaData.translateFromMaxZoomLevel(box.x);
        divaOuter.scrollLeft(boxLeft - (divaOuter.width() / 2) + (box.w / 2) + leftMarginConsiderations);
        // Will include the padding between pages for best results
    },

    /*
     DivaView helpers
     */

    /**
     * Takes an image file name and returns the folio code.
     *
     * @param imageName Some image name, ex: "folio_001.jpg"
     * @returns string "001"
     */
    imageNameToFolio: function(imageName)
    {
        var splitFolioName = String(imageName).split('.')[0].split('_');
        return splitFolioName[splitFolioName.length - 1];
    }
});
});