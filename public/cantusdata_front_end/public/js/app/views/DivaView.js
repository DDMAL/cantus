define( ['App', 'backbone', 'marionette', 'jquery', "diva", "diva-highlight",
        "views/CantusAbstractView",
        "singletons/GlobalEventHandler",
        "config/GlobalVars"],
    function(App, Backbone, Marionette, $, Diva, DivaHighlight,
             CantusAbstractView,
             GlobalEventHandler,
             GlobalVars) {

        "use strict";

        /**
         * Provide an alert message to the user.
         */
        return CantusAbstractView.extend
        ({
            el: "#diva-wrapper",

            divaInitialized: false,

            // Only used if initial folio
            initialFolio: undefined,

            currentFolioIndex: -1,
            currentFolioName: 0,

            imagePrefix: null,
            imageSuffix: "",

            timer: null,

            // Diva Event handlers
            viewerLoadEvent: null,
            pageChangeEvent: null,
            modeSwitchEvent: null,

            initialize: function(options)
            {
                console.log("Initialize Diva View begin.");
                _.bindAll(this, 'render', 'storeFolioIndex', 'storeInitialFolio',
                    'setGlobalFullScreen', 'zoomToLocation');
                this.el = options.el;
                this.setManuscript(options.siglum, options.folio);
                console.log("Initialize Diva View end.");
            },

            /**
             * Destroy Diva instance.
             */
            remove: function()
            {
                // Deal with the event listeners
                this.stopListening();
                this.undelegateEvents();
                // Clear the fields
                this.initialFolio = null;
                this.currentFolioName = null;
                this.currentFolioIndex = null;
                this.imagePrefix = null;
                this.imageSuffix = null;
                this.timer = null;
                this.viewerLoadEvent = null;
                this.modeSwitchEvent = null;
            },

            /**
             * Destroy the Diva viewer, if it exists.
             */
            uninitializeDiva: function()
            {
                if (this.divaInitialized)
                {
                    // Unsubscribe the event handlers
                    if (this.viewerLoadEvent !== null)
                    {
                        diva.Events.unsubscribe(this.viewerLoadEvent);
                    }
                    if (this.pageChangeEvent !== null)
                    {
                        diva.Events.unsubscribe(this.pageChangeEvent);
                    }
                    if (this.modeSwitchEvent !== null)
                    {
                        diva.Events.unsubscribe(this.modeSwitchEvent);
                    }
                }
            },

            /**
             * Initialize Diva and subscribe to its events.
             */
            initializeDiva: function()
            {
                console.log("initailizeDiva() state");
                var siglum = this.siglum;
                console.log("siglum:", siglum);
                this.$el.diva({
                    toolbarParentSelector: "#diva-toolbar",
                    viewerWidthPadding: 0,
                    enableAutoTitle: false,
                    enableAutoWidth: false,
                    enableAutoHeight: false,
                    enableFilename: false,
                    enableHighlight: true,
                    fixedHeightGrid: false,
                    enableCanvas: true,
                    iipServerURL: GlobalVars.iipImageServerUrl + "fcgi-bin/iipsrv.fcgi",
                    objectData: "/static/" + siglum + ".json",
                    imageDir: GlobalVars.divaImageDirectory + siglum
                });
                // console.log("this.el:", this.el);
                // console.log("this.$el:", this.$el);
                this.viewerLoadEvent = diva.Events.subscribe("ViewerDidLoad", this.storeInitialFolio);
                this.pageChangeEvent = diva.Events.subscribe("VisiblePageDidChange", this.storeFolioIndex);
                this.modeSwitchEvent = diva.Events.subscribe("ModeDidSwitch", this.setGlobalFullScreen);
                // Remember that we've initialized diva
                this.divaInitialized = true;
                console.log("initailizeDiva() end");
            },

            render: function()
            {
                //console.log("Diva render() begin.");
                // We only want to initialize Diva once!
                if (!this.divaInitialized)
                {
                    this.initializeDiva();
                }

                GlobalEventHandler.trigger("renderView");
                //console.log("Diva render() end.");
                return this.trigger('render', this);
            },

            setGlobalFullScreen: function(isFullScreen)
            {
                if (isFullScreen === true)
                {
                    GlobalEventHandler.trigger("divaFullScreen");
                }
                else if (isFullScreen === false)
                {
                    GlobalEventHandler.trigger("divaNotFullScreen");
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
             * Store the index and filename of the first loaded page.
             */
            storeInitialFolio: function()
            {
                //console.log("storeInitialFolio() begin.");
                // If there exists a client-defined initial folio
                if (this.initialFolio !== undefined)
                {
                    this.setFolio(this.initialFolio);
                }
                // Grab data from diva
                var divaData = this.getDivaData();
                // Store the initial folio
                debugger;
                var number = divaData.getCurrentPageIndex();
                var name = divaData.getCurrentPageFilename();
                this.storeFolioIndex(number, name);
                // Store the image prefix for later
                this.setImagePrefixAndSuffix(name);
                //console.log("storeInitialFolio() end.");
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
                //console.log("storeFolioIndex() begin.");
                // The first time it's ever called
                if (this.initialFolio === undefined) {
                    this.initialFolio = 0;
                }
                // Not the first time
                else if (index !== this.currentFolioIndex)
                {
                    this.currentFolioIndex = index;
                    this.currentFolioName = fileName;

                    if (this.timer !== null)
                    {
                        window.clearTimeout(this.timer);
                    }

                    this.timer = window.setTimeout(
                        function ()
                        {
                            GlobalEventHandler.trigger("manuscriptChangeFolio");
                        },
                        250);
                }
                //console.log("storeFolioIndex() end.");
            },

            /**
             * Get the stored Diva data.
             *
             * @returns {*|jQuery}
             */
            getDivaData: function() {
                return $(this.el).data('diva');
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

                var topMarginConsiderations = divaData.getSettings().averageHeights[zoomLevel] * divaData.getSettings().adaptivePadding;
                var leftMarginConsiderations = divaData.getSettings().averageWidths[zoomLevel] * divaData.getSettings().adaptivePadding;
                divaOuter.scrollTop(boxTop + currentScrollTop - (divaOuter.height() / 2) + (box.h / 2) + topMarginConsiderations);
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