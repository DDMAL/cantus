(function($){

    var siteUrl = "/";
    var iipImageServerUrl = "http://cantus.simssa.ca/";
    var divaImageDirectory = "/srv/images/cantus/";

    // Global Event Handler for global events
    var globalEventHandler = {};
    _.extend(globalEventHandler, Backbone.Events);


    /**
     * This object handles resizing the browser
     *
     *
     * @type {{setContainerHeight: setContainerHeight, setScrollableHeight: setScrollableHeight, setManuscriptContentContainerHeight: setManuscriptContentContainerHeight, setDivaHeight: setDivaHeight}}
     */
    var BrowserResizer = Backbone.View.extend
    ({

        divaFullScreen: null,
        timedQuery: null,

        initialize: function()
        {
            _.bindAll(this, 'timedQuerySetAll', 'setAll', 'setContainerHeight',
                'setScrollableHeight', 'setManuscriptContentContainerHeight',
            'setDivaSize', 'setDivaFullScreen');
            var self = this;
            $(window).resize(function()
            {
                self.timedQuerySetAll();
            });
            this.divaFullScreen = "lol";
            this.listenTo(globalEventHandler, "renderView",
                this.timedQuerySetAll);
            this.listenTo(globalEventHandler, "divaFullScreen",
                function(){this.setDivaFullScreen(true);});
            this.listenTo(globalEventHandler, "divaNotFullScreen",
                function(){this.setDivaFullScreen(false);});
        },

        /**
         * Set a timed query for resizing the window.
         */
        timedQuerySetAll: function()
        {
            window.clearTimeout(this.timedQuery);
            this.timedQuery = window.setTimeout(this.setAll, 250);
        },

        setAll: function()
        {
            this.setContainerHeight();
            this.setManuscriptContentContainerHeight();
            this.setDivaSize();
        },

        setContainerHeight: function()
        {
            $('#content-container').css("height",
                    $(window).height() - $("#header-container").height());
        },

        setScrollableHeight: function()
        {
            $('.scrollable').css("height", $("#content-container").height());
        },

        setManuscriptContentContainerHeight: function()
        {
            $('#manuscript-data-container').css("height",
                    $("#content-container").height()
                            - $("#manuscript-title-container").height());
        },

        setDivaSize: function()
        {
            if (this.divaFullScreen !== true)
            {
                $('.diva-outer').css("height",
                        $("#content-container").height() - 75);
            }
        },

        /**
         * Resize the Diva viewer into fullscreen mode when necessary
         *
         * @param isFullScreen
         */
        setDivaFullScreen: function(isFullScreen)
        {
            if (isFullScreen === true)
            {
                this.divaFullScreen = true;
            }
            else if (isFullScreen === false)
            {
                this.divaFullScreen = false;
            }
            this.setDivaSize();
        }
    });

    var resizer = new BrowserResizer();

    /**
     * Handles the global state.  Updates URLs.
     */
    var GlobalStateModel = Backbone.Model.extend
    ({
        manuscript: undefined,
        folio: undefined,
        chant: undefined,

        initialize: function()
        {
            _.bindAll(this, "setManuscript", "setFolio", "setChant", "silentUrlUpdate");
            this.listenTo(globalEventHandler, 'ChangeManuscript', this.setManuscript);
            this.listenTo(globalEventHandler, 'ChangeFolio', this.setFolio);
            this.listenTo(globalEventHandler, 'ChangeChant', this.setChant);
            this.listenTo(globalEventHandler, 'SilentUrlUpdate', this.silentUrlUpdate);
        },

        setManuscript: function(manuscript)
        {
            this.manuscript = manuscript;
        },

        setFolio: function(folio)
        {
            this.folio = folio;
        },

        setChant: function(chant)
        {
            this.chant = chant;
        },

        getUrl: function()
        {
            var composed_url = "manuscript/" + this.manuscript + "/";
            if (this.folio !== undefined && this.folio !== null)
            {
                composed_url = composed_url + "?folio=" + this.folio;
            }
            if (this.chant !== undefined && this.chant !== null)
            {
                composed_url = composed_url + "&chant=" + this.chant;
            }
            return composed_url;
        },

        silentUrlUpdate: function()
        {
            // Don't actually trigger the router!
            app.navigate(this.getUrl(), {trigger: false});
        }
    });

    /*
    Helper Objects
     */

    /**
    * An object that acts like a big row of switches.  You can call
    * getValue() to get the index of the first true element.
    */
    StateSwitch = Backbone.Model.extend
    ({

        length: 0,
        valueArray: undefined,

        initialize: function(length)
        {
            this.valueArray = [];
            this.length = parseInt(length);
            for (var i = 0; i < this.length; i++)
            {
                this.valueArray.push(false);
            }
        },

        /**
         * Set a value.
         *
         * @param index int
         * @param value boolean
         */
        setValue: function(index, value)
        {
            // Handle out-of-bounds cases
            if (index < 0)
            {
                index = 0;
            }
            else if (index >= this.length)
            {
                index = this.length - 1;
            }
            // Set the value
            this.valueArray[index] = value;
        },

        /**
         * Return the index of the true element.
         *
         * @returns {*}
         */
        getValue: function()
        {
            for (var i = 0; i < this.length; i++)
            {
                if (this.valueArray[i] === true)
                {
                    return i;
                }
            }
            // No elements are true!
            return undefined;
        }
    });

    var SolrDisjunctiveQueryBuilder = Backbone.Model.extend
    ({
        field: undefined,
        values: undefined,

        initialize: function(field, values)
        {
            this.field = String(field);
            this.values = [];
            for (var i = 0; i < values.length; i++)
            {
                this.addValue(values[i]);
            }
        },

        /**
         * Add a value to the disjunctive query.
         *
         * @param value
         */
        addValue: function(value)
        {
            this.values.push(String(value));
        },

        /**
         * Construct the query.
         *
         * @returns {string}
         */
        getQuery: function()
        {
            var output = this.field + ": (";

            if (this.values.length > 0)
            {
                // The first value
                output += ('"' + this.values[0] + '"');
                // The rest
                for (var i = 1; i < this.values.length; i++)
                {
                    output += (' OR "' + this.values[i] + '"');
                }
            }

            return output + ")";
        }
    });

    /*
    Models
     */

    var CantusAbstractModel = Backbone.Model.extend
    ({
        initialize: function(url)
        {
            this.url = url;
        }
    });

    var Chant = CantusAbstractModel.extend
    ({
//        defaults: function()
//        {
//            return {
//                marginalia: "the marginalia",
//                folio: "the folio",
//                sequence:"the sequence",
//                cantus_id: "the cantus id",
//                feast: "the feast",
//                office: "the office",
//                genre: "the genre",
//                lit_position: "the lit position",
//                mode: "the mode",
//                differentia: "the differentia",
//                finalis: "the finalis",
//                incipit: "the incipit",
//                full_text: "Quite a nice chant!",
//                concordances: [],
//                volpiano: "the volpiano",
//                manuscript: "the manuscript"
//            }
//        }
    });

    var Concordance = CantusAbstractModel.extend
    ({
//        defaults: function()
//        {
//            return {
//                letter_code: "ZZZ",
//                institution_city: "Montreal",
//                instutition_name: "DDMAL",
//                library_manuscript_name: "No Name",
//                date: "Right now",
//                location: "Montreal",
//                rism_code: "ABC1234"
//            }
//        }
    });

    var Folio = CantusAbstractModel.extend
    ({
//        defaults: function()
//        {
//            return {
//                number: "000",
//                manuscript: null,
//                chant_count: 0,
//                chant_set: []
//            }
//        }
    });

    var Manuscript = CantusAbstractModel.extend
    ({
//        defaults: function()
//        {
//            return {
//                url: "#",
//                name: "Test Name",
//                siglum: "Test Siglum",
//                siglum_slug: "#",
//                date: "Tomorrow",
//                provenance: "Test provenance",
//                description: "This is a nice manuscript...",
//                chant_count: 5
//            };
//        }
    });

    /**
     * This represents a search result.  It is experimental.
     */
    var SearchResult = Backbone.Model.extend
    ({
        // Sometimes overridden
        searchPage: "search/?q=",

        initialize: function(pQuery)
        {
            this.setQuery(pQuery);
        },

        setQuery: function(query)
        {
            this.url = siteUrl + this.searchPage + query;
        },

        /**
         * Formats the data to be printed in a search result list.
         */
        getFormattedData: function()
        {
            var output = [];

            _.each(this.toJSON().results, function(current)
            {
                var newElement = {};
                // Remove "cantusdata_" from the type string
                newElement.model = current.type.split("_")[1];
                newElement.name = current.Name;

                // Figure out what the name is based on the model in question
                switch(newElement.model)
                {
                    case "manuscript":
                        newElement.name = current.name;
                        // Build the url
                        newElement.url = "/" + newElement.model
                            + "/" + current.item_id + "/";
                        break;

                    case "chant":
                        newElement.name = current.incipit;
                        // Build the url
                        // We have stored the manuscript name in Solr
                        newElement.manuscript = current.manuscript_name_hidden;
                        newElement.folio = current.folio;
                        newElement.volpiano = current.volpiano;
                        newElement.url = "/manuscript/" + current.manuscript_id
                            + "/?folio=" + current.folio
                            + "&chant=" + current.sequence;
                        break;

                    case "concordance":
                        newElement.name = current.name;
                        // Build the url
                        newElement.url = "/" + newElement.model
                            + "/" + current.item_id + "/";
                        break;

                    case "folio":
                        newElement.name = current.name;
                        // Build the url
                        newElement.url = "/" + newElement.model
                            + "/" + current.item_id + "/";
                        break;
                }
                output.push(newElement);
            });
            return output;
        },

        /**
         * An empty search is empty.
         */
        defaults: function()
        {
            return {
                results: []
            };
        }
    });


    /*
    Collections
     */

    var CantusAbstractCollection = Backbone.Collection.extend
    ({
        initialize: function(url)
        {
            if (url) {
                this.url = url;
            }
        },

        defaults: function()
        {
            return [];
        }
    });

    var ChantCollection = CantusAbstractCollection.extend
    ({
        model: Chant
    });

    var ConcordanceCollection = CantusAbstractCollection.extend
    ({
        model: Concordance
    });

    var FolioCollection = CantusAbstractCollection.extend
    ({
        model: Folio
    });

    var ManuscriptCollection = CantusAbstractCollection.extend
    ({
        model: Manuscript
    });


    /*
    Component Views
    */

    var CantusAbstractView = Backbone.View.extend
    ({
        /**
         * Used to render subviews.
         *
         * @param view The view object to be rendered
         * @param selector The html selector where you want to render the view
         */
        assign : function (view, selector) {
            view.setElement(selector).render();
        },

        unAssign : function (view, selector) {
            $(selector).empty();
        }
    });

    var ChantCollectionView = CantusAbstractView.extend
    ({
        /**
         * Useful switch if you want different functionality on initial load.
         */
        alreadyLoaded: false,

        /**
         * The chant that bootstrap has unfolded!
         */
        unfoldedChant: undefined,

        chantStateSwitch: undefined,

        events: {
            'hidden.bs.collapse': 'foldChantCallback',
            'show.bs.collapse': 'unfoldChantCallback'
        },

        initialize: function()
        {
            _.bindAll(this, 'render', 'setUnfoldedChant', 'unfoldChantCallback',
                'foldChantCallback', 'afterFetch');
            this.template = _.template($('#chant-collection-template').html());
            this.emptyTemplate = _.template($('#empty-chant-collection-template').html());

            this.collection = new ChantCollection();

            // TODO: Figure out why this is still rendering multiple times
            this.listenTo(this.collection, 'sync', this.render);
            // Set the unfolded chant when the global state changes!
            this.listenTo(globalEventHandler, "ChangeChant", this.setUnfoldedChant);

            this.alreadyLoaded = 0;
        },

        /**
         * Callback for when a chant is "unfolded" by Bootstrap.
         *
         * @param event
         */
        unfoldChantCallback: function(event)
        {
            // "collapse-1" becomes 1, etc.
            var chant = parseInt(event.target.id.split('-')[1]) + 1;
            this.chantStateSwitch.setValue(chant, true);

            globalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue());
            globalEventHandler.trigger("SilentUrlUpdate");
        },

        foldChantCallback: function(event)
        {
            var chant = parseInt(event.target.id.split('-')[1]) + 1;
            this.chantStateSwitch.setValue(chant, false);

            globalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue());
            globalEventHandler.trigger("SilentUrlUpdate");
        },

        /**
         * Set the "unfolded" chant.
         *
         * @param index 0 to infinity
         */
        setUnfoldedChant: function(index)
        {
            if (index !== undefined && index !== null)
            {
                this.unfoldedChant = parseInt(index) - 1;
            }
        },

        afterFetch: function()
        {
            // Make a new StateSwitch object that we will use to keep track
            // of the open chant.
            this.chantStateSwitch = new StateSwitch(this.collection.length);
        },

        /**
         * Set the URL of the collection and fetch the data.
         *
         * @param url
         * @param unfoldedChant
         */
        setUrl: function(url, unfoldedChant)
        {
            this.collection.url = url;
            this.collection.fetch({success: this.afterFetch});
            // Reset the chant if this isn't the initial load
            if (this.alreadyLoaded) {
                this.unfoldedChant = undefined;
                globalEventHandler.trigger("ChangeChant", undefined);
                globalEventHandler.trigger("SilentUrlUpdate");
            }
            else
            {
                this.alreadyLoaded = true;
            }
        },

        /**
         * Render the collection.
         *
         * @returns {*}
         */
        render: function()
        {
            // TODO: Figure out why this gets called 4 times
            if (this.collection.length === 0)
            {
                $(this.el).html(this.emptyTemplate());
            }
            else
            {
                // Render out the template
                $(this.el).html(this.template(
                    {
                        chants: this.collection.toJSON(),
                        unfoldedChant: this.unfoldedChant
                    }
                ));
            }
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        },

        resetCollection: function()
        {
            this.collection.reset();
        }
    });

    var DivaView = CantusAbstractView.extend
    ({
        divaInitialized: false,

        // Only used if initial folio
        initialFolio: undefined,

        currentFolioIndex: -1,
        currentFolioName: 0,

        imagePrefix: "",
        imageSuffix: "",

        timer: null,

        // Diva Event handlers
        viewerLoadEvent: null,
        pageChangeEvent: null,
        modeSwitchEvent: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'storeFolioIndex', 'storeInitialFolio',
                'setGlobalFullScreen', 'zoomToLocation');
            this.setManuscript(options.siglum, options.folio);
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
            var siglum = this.siglum;
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
                iipServerURL: iipImageServerUrl + "fcgi-bin/iipsrv.fcgi",
                objectData: "/static/" + siglum + ".json",
                imageDir: divaImageDirectory + siglum
            });
            this.viewerLoadEvent = diva.Events.subscribe("ViewerDidLoad", this.storeInitialFolio);
            this.pageChangeEvent = diva.Events.subscribe("VisiblePageDidChange", this.storeFolioIndex);
            this.modeSwitchEvent = diva.Events.subscribe("ModeDidSwitch", this.setGlobalFullScreen);
            // Remember that we've initialized diva
            this.divaInitialized = true;
        },

        render: function()
        {
            // We only want to initialize Diva once!
            if (!this.divaInitialized)
            {
                this.initializeDiva();
            }

            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        },

        setGlobalFullScreen: function(isFullScreen)
        {
            if (isFullScreen === true)
            {
                globalEventHandler.trigger("divaFullScreen");
            }
            else if (isFullScreen === false)
            {
                globalEventHandler.trigger("divaNotFullScreen");
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
            // If there exists a client-defined initial folio
            if (this.initialFolio !== undefined)
            {
                this.setFolio(this.initialFolio);
            }
            // Store the initial folio
            var number = this.$el.data('diva').getCurrentPageIndex();
            var name = this.$el.data('diva').getCurrentPageFilename();
            this.storeFolioIndex(number, name);
            // Store the image prefix for later
            this.setImagePrefixAndSuffix(name);
        },

        /**
         * Takes an image file name and returns the folio code.
         *
         * @param imageName Some image name, ex: "folio_001.jpg"
         * @returns string "001"
         */
        imageNameToFolio: function (imageName)
        {
            var splitFolioName = String(imageName).split('.')[0].split('_');
            return splitFolioName[splitFolioName.length - 1];
        },

        /**
         * Sets this.imagePrefix from any image name.
         *
         * @param imageName
         */
        setImagePrefixAndSuffix: function (imageName)
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
            if (this.imagePrefix === "" || this.imageSuffix === "")
            {
                this.setImagePrefixAndSuffix(this.currentFolioName);
            }
            var newImageName = this.imagePrefix + "_" + String(folioCode) + "." + this.imageSuffix;
            if (this.$el.data('diva') !== undefined)
            {
                this.$el.data('diva').gotoPageByName(newImageName);
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
            if (index !== this.currentFolioIndex)
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
                        globalEventHandler.trigger("manuscriptChangeFolio");
                    },
                    250);
            }
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
            this.$el.data('diva').resetHighlights();

            // Use the Diva highlight plugin to draw the boxes
            var highlightsByPageHash = {};
            var pageList = [];

            for (var i = 0; i < boxSet.length; i++)
            {
                var page = boxSet[i].p - 1; // The page

                if (highlightsByPageHash[page] === undefined)
                {
                    // Add page to the hash
                    highlightsByPageHash[page] = [];
                    pageList.push(page);

                }
                // Page is in the hash, so we add to it.
                highlightsByPageHash[page].push
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
                this.$el.data('diva').highlightOnPage
                (
                    pageList[j], // The page number
                    highlightsByPageHash[pageList[j]] // List of boxes
                );
            }
        },

        /**
         * Zoom Diva to a location
         * 
         * @param {type} box
         * @returns null
         */
        zoomToLocation: function(box)
        {
            if (box === undefined)
            {
                // Do nothing if no box!
                return;
            }

            // Now figure out the page that box is on
            var divaOuter = this.$el.data('diva').getSettings().outerSelector;
            var desiredPage = box.p;
            var zoomLevel = this.$el.data('diva').getZoomLevel();

            // Now jump to that page
            this.$el.data('diva').gotoPageByNumber(desiredPage);
            // Get the height above top for that box
            var boxTop = this.$el.data('diva').translateFromMaxZoomLevel(box.y);
            var currentScrollTop = parseInt($(divaOuter).scrollTop(), 10);

            var topMarginConsiderations = this.$el.data('diva').getSettings().averageHeights[zoomLevel]
                * this.$el.data('diva').getSettings().adaptivePadding;
             var leftMarginConsiderations = this.$el.data('diva').getSettings().averageWidths[zoomLevel]
                * this.$el.data('diva').getSettings().adaptivePadding;
             $(divaOuter).scrollTop(boxTop + currentScrollTop -
                ($(divaOuter).height() / 2) + (box.h / 2) + topMarginConsiderations);
            // Now get the horizontal scroll
            var boxLeft = this.$el.data('diva').translateFromMaxZoomLevel(box.x);
            $(divaOuter).scrollLeft(boxLeft - ($(divaOuter).width() / 2)
                + (box.w / 2) + leftMarginConsiderations);
            // Will include the padding between pages for best results
        }
    });

    var FolioView = CantusAbstractView.extend
    ({
        /**
         * customNumber is the folio number that we actually render.
         */
        customNumber: 0,

        // Subviews
        chantCollectionView: null,

        /**
         * 
         * 
         * @param {type} options
         * @returns null
         */
        initialize: function(options)
        {
            _.bindAll(this, 'render', 'afterFetch', 'assignChants');
            this.template= _.template($('#folio-template').html());
            // This can handle situations where the first folio
            // doesn't have a url but subsequent ones do.
            if (options && options.url)
            {
                this.setUrl(options.url);
            }
            else
            {
                this.model = new Folio();
                this.listenTo(this.model, 'sync', this.afterFetch);
            }
            this.chantCollectionView = new ChantCollectionView();
        },

        remove: function()
        {
            this.chantCollectionView.remove();

            // Deal with the event listeners
            this.stopListening();
            this.undelegateEvents();
        },

        /**
         * Set the model URL.
         *
         * @param url
         */
        setUrl: function(url)
        {
            this.model = new Folio(url);
            this.listenTo(this.model, 'sync', this.afterFetch);
        },

        /**
         * Set the parameter that overrides the number that's rendered to the
         * screen.
         *
         * @param number
         */
        setCustomNumber: function(number)
        {
            this.customNumber = number;
        },

        /**
         * Fetch the latest version of the model.
         */
        update: function()
        {
            this.model.fetch();
        },

        /**
         * If the model is empty, un-render the view.  Otherwise, assign
         * the chants and render the view.
         */
        afterFetch: function()
        {
            this.assignChants();
            this.render();
        },

        /**
         * Rebuild the list of chants
         */
        assignChants: function()
        {
            // We are going to query this data from SOLR because it's faster.
            // So we need the manuscript siglum and folio name.
            // We need to handle the data differently depending on whether
            // we're getting the information from Django or Solr.
            var folio_id;
            if (this.model.toJSON().item_id)
            {
                folio_id = this.model.toJSON().item_id;
            }
            else
            {
               folio_id = this.model.toJSON().id;
            }

            if (folio_id !== undefined)
            {
                // Compose the url
                var composedUrl = siteUrl + "chant-set/folio/" + folio_id + "/";
                // Build a new view with the new data
                this.chantCollectionView.setUrl(composedUrl);
            }
            else
            {
                this.chantCollectionView.resetCollection();
            }
        },

        render: function()
        {
            $(this.el).html(this.template(
                {
                    number: this.customNumber,
                    model: this.model.toJSON()
                }
            ));
            this.renderChantCollectionView();
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        },

        /**
         * Render the collection of chants.
         */
        renderChantCollectionView: function()
        {
            if (this.chantCollectionView !== null)
            {
                this.assign(this.chantCollectionView, '#chant-list');
            }
        }
    });

    var HeaderView = CantusAbstractView.extend
    ({
        // Subviews
        topMenuView: null,
        searchView: null,
        searchModalView: null,

        events: {
            "click #site-logo": function()
            {
                // Prevent page from reloading
                event.preventDefault();
                app.navigate("/", {trigger: true});
            }
        },

        initialize: function()
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#header-template').html());
            // The search view that we will shove into the modal box
            this.searchView = new SearchView({showManuscriptName: true});
            // The modal box for the search pop-up
            this.searchModalView = new ModalView({title: "Search", view: this.searchView});
            // Create the TopMenuView with all of its options
            this.topMenuView = new TopMenuView(
                {
                    menuItems: [
                        {
                            name: "Manuscripts",
                            url: "/",
                            active: false
                        },
                        {
                            name: "Search",
                            tags: 'data-toggle="modal" data-target="#myModal"',
                            url: "#",
                            active: false
                        }
                    ]
                }
            );
        },

        render: function()
        {
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.topMenuView, '#top-menu');
            this.assign(this.searchModalView, '#search-modal');
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    var TopMenuView = CantusAbstractView.extend
    ({
        activeButton: 0,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'registerClickEvents', "buttonClickCallback");
            this.template= _.template($('#top-menu-template').html());
            // Menu list items provided
            this.items = options.menuItems;
            this.registerClickEvents();
        },

        /**
         * Whenever a menu item is clicked, we want to push the state
         */
        registerClickEvents: function()
        {
            // Clear out the events
            this.events = {};
            // Menu items
            for (var i = 0; i < this.items.length; i++)
            {
                this.events["click #top-menu-button-" + i] = "buttonClickCallback";
            }
            // Delegate the new events
            this.delegateEvents();
        },

        buttonClickCallback: function(input)
        {
            // Stop the page from auto-reloading
            event.preventDefault();
            // Figure out which button was pressed
            var button_name = String(input.currentTarget.id);
            var id = button_name.split('-')[button_name.split('-').length - 1];
            // Now that we have that id, route the application to it's URL!
            var new_url = this.items[id].url;
            var old_url = Backbone.history.fragment;
            // Only route to the new URL if it really is a new url!
            if (!(new_url === "#" || new_url.trim('/') === old_url.trim('/')))
            {
                app.navigate(this.items[id].url, {trigger: true});
                this.setActiveButton(id);
            }
        },

        /**
         * Set which menu button is active at the moment.
         *
         * @param index
         */
        setActiveButton: function(index)
        {
            if (index === this.activeButton) return;
            this.items[this.activeButton].active = false;
            this.activeButton = index;
            this.items[this.activeButton].active = true;
            this.render();
        },

        render: function()
        {
            $(this.el).html(this.template({items: this.items}));
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    var ManuscriptCollectionView = CantusAbstractView.extend
    ({
        collection: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'update', 'registerClickEvents',
                'buttonClickCallback');
            this.template= _.template($('#manuscript-collection-template').html());
            this.collection = new ManuscriptCollection(options.url);
            this.listenTo(this.collection, 'sync', this.registerClickEvents);
            this.listenTo(this.collection, 'sync', this.render);
        },

        registerClickEvents: function()
        {
            // Clear out the events
            this.events = {};
            // Menu items
            for (var i = 0; i < this.collection.toJSON().length; i++)
            {
                this.events["click #manuscript-list-" + i] = "buttonClickCallback";
            }
            // Delegate the new events
            this.delegateEvents();
        },

        buttonClickCallback: function(input)
        {
            // Prevent page from reloading
            event.preventDefault();
            // Figure out which button was pressed
            var button_name = String(input.currentTarget.id);
            var id = button_name.split('-')[button_name.split('-').length - 1];
            // Now that we have that id, route the application to it's URL!
            var newUrl = "manuscript/" + this.collection.toJSON()[id].id + "/";
            var oldUrl = Backbone.history.fragment;

            // Only route to the new URL if it really is a new url!
            if (newUrl === "#" || newUrl.trim('/') === oldUrl.trim('/'))
            {
                return;
            }
            else
            {
                app.navigate(newUrl, {trigger: true});
            }
        },

        update: function()
        {
            this.collection.fetch();
        },

        render: function()
        {
            $(this.el).html(this.template({
                manuscripts: this.collection.toJSON()
            }));
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    /**
     * Draw a modal box containing a particular view.
     * This view follows the visitor design pattern.
     *
     * @type {*|void}
     */
    var ModalView = CantusAbstractView.extend
    ({
        title: null,
        visitorView: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template = _.template($('#modal-template').html());

            this.title = options.title;
            this.visitorView = options.view;
        },

        render: function()
        {
            // Render out the modal template
            if (this.visitorView !== null)
            {
                $(this.el).html(this.template({title: this.title}));
            }
            // Render out the visitor
            this.assign(this.visitorView, '.modal-body');
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    /**
     * A simple paginator that fires events when it changes page.
     * Page indexes start at 1.
     *
     * @type {*|void}
     */
    var PaginationView = CantusAbstractView.extend
    ({
        name: null,
        elementCount: 1,
        pageCount: 1,
        pageSize: 10,

        // Used for rendering
        currentPage: 1,
        startPage: 1,
        endPage: 1,
        maxWidth: 9,

        events: {},

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'setPage', 'increment', 'decrement',
                'render', 'buttonClick');
            this.template = _.template($('#pagination-template').html());

            this.name = options.name;

            // Set the size and the current
            this.elementCount = options.elementCount;
            this.pageSize = options.pageSize;

            // Calculate number of pages
            this.pageCount = Math.floor(this.elementCount / this.pageSize);
            if (this.elementCount % this.pageSize !== 0)
            {
                this.pageCount++;
            }

            // Page must be set after pagecount exists
            this.setPage(options.currentPage);
        },

        /**
         * Register the events that are necessary to have clickable buttons.
         */
        registerEvents: function()
        {
            // Clear out the events
            this.events = {};
            // No binding if there are no elements
            if (this.elementCount === 0) return;
            // Backwards
            if (this.currentPage > 1)
            {
                this.events["click #" + this.name + "-page-back"] = "decrement";
            }
            // Forwards
            if (this.currentPage < this.pageCount)
            {
                this.events["click #" + this.name + "-page-forward"] = "increment";
            }
            // Add the page clickers
            for (var i = this.startPage; i <= this.endPage; i++)
            {
                if (i !== this.currentPage)
                {
                    this.events["click #" + this.name + "-page-" + i] = "buttonClick";
                }
            }
            // Delegate the new events
            this.delegateEvents();
        },

        /**
         * Get the current paginator page.
         *
         * @returns {number} 1 to infinity
         */
        getPage: function()
        {
            return this.currentPage;
        },

        /**
         * Set the page and render.
         *
         * @param page integer
         */
        setPage: function(page)
        {
            if (page < 1)
            {
                this.currentPage = 1;
            }
            else if (page > this.pageCount)
            {
                this.currentPage = this.pageCount;
            }
            else
            {
                this.currentPage = page;
            }

            if (this.pageCount <= this.maxWidth)
            {
                // This is the case where we don't need to scroll through
                // more pages than can fit in the paginator.
                this.startPage = 1;
                this.endPage = this.pageCount;
            }
            else
            {
                // This is the case where there are more pages than can fit
                // In the paginator, so we need to "scroll" through the numbers.
                if (this.currentPage <= Math.floor(((this.maxWidth | 0) / 2)))
                {
                    // This is the case of the first few numbers
                    this.startPage = 1;
                    this.endPage = this.maxWidth;
                }
                else if ((this.pageCount - this.currentPage) <= Math.floor((this.maxWidth | 0) / 2))
                {
                    // This is the case of the last few numbers
                    this.startPage = this.pageCount - this.maxWidth + 1;
                    this.endPage = this.pageCount;
                }
                else
                {
                    // This case should capture most instances where the
                    // current page is somewhere in the "middle" of the paginator"
                    this.startPage = this.currentPage - ((this.maxWidth / 2) | 0);
                    this.endPage = this.currentPage + ((this.maxWidth / 2) | 0);
                }
            }

            this.render();
            // We have to register the events every time we render
            this.registerEvents();
            this.trigger("change");
        },

        /**
         * Go to the next page.
         */
        increment: function()
        {
            this.setPage(this.currentPage + 1);
        },

        /**
         * Go to the previous page.
         */
        decrement: function()
        {
            this.setPage(this.currentPage - 1);
        },

        /**
         * This function gets called when you click on one of the numbered
         * paginator buttons.
         *
         * @param query
         */
        buttonClick: function(query)
        {
            var buttonId = query.target.id;
            var newPage = parseInt(buttonId.split("page-")[1]);
            this.setPage(newPage);
        },

        render: function()
        {
            $(this.el).html(this.template(
                {
                    name: this.name,
                    startPage: this.startPage,
                    endPage: this.endPage,
                    currentPage: this.currentPage
                }
            ));
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    var SearchNotationView = CantusAbstractView.extend
    ({
        query: null,
        field: null,

        results: null,
        divaView: null,
        paginator: null,
        manuscript: undefined,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'registerEvents', 'newSearch',
                'resultFetchCallback', 'zoomToResult');
            this.template = _.template($('#search-notation-template').html());
            // The diva view which we will act upon!
            this.divaView = options.divaView;
            this.results = new CantusAbstractModel();
            this.paginator = new PaginationView({name: "notation-paginator"});
            this.registerEvents();
            this.listenTo(this.results, "sync", this.resultFetchCallback);
        },

        remove: function()
        {
            this.query = null;
            this.results = null;
            this.paginator.remove();
            // We don't actually need to call remove() on this again
            this.divaView = null;
            this.paginator = null;
            this.manuscript = null;
            // Deal with the event listeners
            this.stopListening();
            this.undelegateEvents();
        },

        setManuscript: function(manuscript)
        {
            this.manuscript = manuscript;
        },

        /**
         * Register the events that are necessary to have search input.
         */
        registerEvents: function()
        {
            // Clear out the events
            this.events = {};
            // Register them
            this.events["submit"] = "newSearch";
            // Delegate the new events
            this.delegateEvents();
        },

        newSearch: function()
        {
            // Stop the page from auto-reloading
            event.preventDefault();
            // Grab the query
            this.query  = encodeURIComponent($(this.$el.selector
                + ' .query-input').val());
            // Handle the empty case
            if (this.query  === "")
            {
                // If we pass an empty array, then all boxes are erased.
                this.divaView.paintBoxes([]);
                this.clearResults("<h4>Please enter a search query.</h4>");
            }
            else
            {
                // Grab the field name
                this.field = encodeURIComponent($(this.$el.selector
                    + ' .search-field').val());
                var composedQuery = siteUrl + "notation-search/?q=" + this.query
                    + "&type=" + this.field + "&manuscript=" + this.manuscript;
                this.results.url = composedQuery;
                this.results.fetch();
            }
        },

        resultFetchCallback: function()
        {
            this.divaView.paintBoxes(this.results.toJSON().results);
            // We need a new paginator
            this.paginator = new PaginationView(
                {
                    name: "notation-paginator",
                    currentPage: 1,
                    elementCount: this.results.toJSON().numFound,
                    pageSize: 1
                }
            );
            // Automatically go to the first result
            this.zoomToResult();
            this.listenTo(this.paginator, 'change', this.zoomToResult);

            this.renderResults();
        },

        zoomToResult: function()
        {
            var newIndex = this.paginator.getPage() - 1;
            this.divaView.zoomToLocation(this.results.toJSON().results[newIndex]);
        },

        render: function() {
            $(this.el).html(this.template());
        },

        clearResults: function(message)
        {
            $(this.$el.selector + ' .note-search-results').html(
                message
            );
            $(this.$el.selector + ' .note-pagination').empty();
        },

        renderResults: function()
        {
            $(this.$el.selector + ' .note-search-results').html(
                "<h4>" + this.results.toJSON().numFound +
                    ' results found for query "' + this.field + ':'
                    + decodeURIComponent(this.query) + '"</h4>'
            );
            this.assign(this.paginator, this.$el.selector + ' .note-pagination');
        }
    });

    var SearchView = CantusAbstractView.extend
    ({
        /**
         *
         */
        query: null,
        field: "all",

        /**
         * Some additional text added to all queries.  For example, you might
         * want this view to only search through chants.  In that case,
         * you would set this.queryPostScript to "AND type:cantusdata_chant".
         */
        queryPostScript: null,
        timer: null,

        // Subviews
        searchResultView: null,

        // Search template dictionary
        currentSearchFormTemplate: "all",
        searchFormTemplates: {},

        events: {},

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'newSearch', 'autoNewSearch',
                'changeSearchField', 'registerEvents');
            this.template= _.template($('#search-template').html());
            // The search form templates
            this.searchFormTemplates['all'] = _.template(
                $('#search-all-template').html());
            this.searchFormTemplates['mode'] = _.template(
                $('#search-mode-template').html());
            this.searchFormTemplates['volpiano'] = this.searchFormTemplates['all'];
            this.searchFormTemplates['feast'] = this.searchFormTemplates['all'];
            this.searchFormTemplates['office'] = this.searchFormTemplates['all'];

            // This will be populated in a minute
            var searchResultViewOptions = {};

            // If not supplied, the query is blank
            if (options !== undefined)
            {
                // Is there a query?
                if (options.query !== undefined)
                {
                    this.query = options.query;
                }
                else
                {
                    this.query = "";
                }
                // Add the query to the search result
                searchResultViewOptions.query = this.query;
                // Is there a query post script?
                if (options.queryPostScript !== undefined)
                {
                    this.setQueryPostScript(options.queryPostScript);
                }
                if (options.showManuscriptName !== undefined)
                {
                    searchResultViewOptions.showManuscriptName = options.showManuscriptName;
                }
            }
            this.searchResultView = new SearchResultView(searchResultViewOptions);
        },

        /**
         * Set this.queryPostScript.
         *
         * @param postScript string
         */
        setQueryPostScript: function(postScript)
        {
            this.queryPostScript = String(postScript);
        },

        changeSearchField: function()
        {
            // Grab the field name
            var newField = encodeURIComponent($(this.$el.selector
                + ' .search-field').val());
            // We want to make sure that we aren't just loading the same template again
            if (this.searchFormTemplates[newField] !== this.searchFormTemplates[this.field])
            {
                // Store the field
                this.field = newField;
                // Render with the new template
                $(this.$el.selector  + " .input-section").html(
                    this.searchFormTemplates[String(this.field)](
                        {query: this.query}));
            }
            // We want to fire off a search
            this.newSearch();
        },

        /**
         * Take the value of the search input box and perform a search query
         * with it.  This function hits the API every time it is called.
         */
        newSearch: function()
        {
            // Grab the new search query
            var newQuery = encodeURIComponent($(this.$el.selector
                + ' .search-input').val());
            // Grab the field name
            var fieldSelection = encodeURIComponent($(this.$el.selector
                + ' .search-field').val());
            if (newQuery !== this.query || fieldSelection !== this.field) {
                this.query = newQuery;
                this.field = fieldSelection;
                if (newQuery === "")
                {
                    // Empty search, so hide the searchResultView
                    this.searchResultView.hide();
                }
                else {
                    // Append the field selector if necessary!
                    if (fieldSelection !== "all")
                    {
                        // Split the query into multiple things
                        queryList = decodeURIComponent(newQuery).split(",");
                        var disjunctive = new SolrDisjunctiveQueryBuilder(fieldSelection, queryList);
                        newQuery = disjunctive.getQuery();
                    }
                    if (this.queryPostScript !== null)
                    {
                        // Attach this.queryPostScript if available
                        this.searchResultView.changeQuery(newQuery + " "
                            + this.queryPostScript, this.field);
                    }
                    else
                    {
                        // Set the new search results view
                        this.searchResultView.changeQuery(newQuery, this.field);
                    }
                }
            }
        },

        /**
         * Register the events that are necessary to have search input.
         */
        registerEvents: function()
        {
            // Clear out the events
            this.events = {};
            // Register them
            this.events["change .search-input"] = "newSearch";
            this.events["change .search-field"] = "changeSearchField";
            this.events["input .search-input"] = "autoNewSearch";
            // Delegate the new events
            this.delegateEvents();
        },

        /**
         * Set the timer to perform a new search.
         * This is called when you want to avoid making multiple querie
         * very quickly.
         */
        autoNewSearch: function()
        {
            if (this.timer !== null)
            {
                window.clearTimeout(this.timer);
            }
            this.timer = window.setTimeout(this.newSearch, 250);
        },

        render: function()
        {
            this.registerEvents();
            $(this.el).html(this.template());
            if (this.field in this.searchFormTemplates)
            {
                $(this.$el.selector  + " .input-section").html(
                    this.searchFormTemplates[this.field]({query: this.query}));
            }
            else
            {
                $(this.$el.selector  + " .input-section").html("Error!");
            }
            // Render subviews
            $(this.$el.selector + ' .search-results').html("SEARCH RESULT VIEW!");
            this.assign(this.searchResultView, this.$el.selector + ' .search-results');
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    var SearchResultView = CantusAbstractView.extend
    ({
        showManuscriptName: null,
        pageSize: 10,
        currentPage: null,
        paginationView: null,
        query: null,
        field: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'updatePage', 'changeQuery',
                'updatePaginationView', 'registerClickEvents',
                'buttonClickCallback');
            this.template = _.template($('#search-result-template').html());
            this.currentPage = 1;
            this.model = new SearchResult();

            if (options.query !== undefined)
            {
                this.model.setQuery(options.query);
                this.query = options.query;
            }
            if (options.showManuscriptName !== undefined)
            {
                // The client might not want to see the manuscript name
                this.showManuscriptName = options.showManuscriptName;
            }

            // Query the search result
            this.model.fetch({success: this.updatePaginationView});
            this.listenTo(this.model, 'sync', this.registerClickEvents);
            this.listenTo(this.model, 'sync', this.render);
        },

        /**
         * Register the events for clicking on a search result.
         */
        registerClickEvents: function()
        {
            // Clear out the events
            this.events = {};
            // Menu items
            for (var i = 0; i < this.model.toJSON().results.length; i++)
            {
                this.events["click .search-result-" + i]
                    = "buttonClickCallback";
            }
            // Delegate the new events
            this.delegateEvents();
        },

        buttonClickCallback: function(input)
        {
            // Stop the page from auto-reloading
            event.preventDefault();
            // Figure out which button was clicked on
            var splitName = input.target.className.split("-");
            var newIndex = parseInt(splitName[splitName.length - 1]);
            // Redirect us to the new url!
            app.navigate(this.model.getFormattedData()[newIndex].url,
                {trigger: true});
        },

        /**
         * Set the model's query string and fetch results from the restful API.
         *
         * @param query string
         * @param field string
         */
        changeQuery: function(query, field)
        {
            this.currentPage = 1;
            this.model.setQuery(query);
            this.query = String(query);
            this.field = String(field);
            this.model.fetch({success: this.updatePaginationView});
        },

        /**
         * Rebuild the pagination view with the latest data from the model.
         */
        updatePaginationView: function()
        {
            this.paginationView = new PaginationView(
                {
                    name: "search",
                    currentPage: this.currentPage,
                    elementCount: this.model.toJSON().numFound,
                    pageSize: this.pageSize
                }
            );
            this.listenTo(this.paginationView, 'change', this.updatePage);
        },

        /**
         * Grab the page number from the paginator
         */
        updatePage: function()
        {
            // Grab the page
            this.currentPage = this.paginationView.getPage();
            // Rebuild the model with a modified query
            this.model.setQuery(this.query + "&start="
                + (this.pageSize * (this.currentPage - 1)));
            this.model.fetch();
        },

        render: function()
        {
            // Only render if the model is defined
            if (this.model !== undefined)
            {
                console.log("Showmanuscriptname: ", this.showManuscriptName)
                $(this.el).html(this.template(
                    {
                        showManuscriptName: this.showManuscriptName,
                        searchType: this.field,
                        results: this.model.getFormattedData()
                    }
                ));
                if (this.model.getFormattedData().length !== 0 && this.paginationView !== null)
                {
                    this.assign(this.paginationView, this.$el.selector + " .pagination");
                }
            }
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        },

        hide: function()
        {
            $(this.el).html(this.template({results: []}));
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });


    /*
    Generic widget views.
     */

    /**
     * Provide an alert message to the user.
     */
    var AlertView = CantusAbstractView.extend
    ({
        alertRoles: ["success", "info", "warning", "danger"],

        role: "info",
        content: undefined,

        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template = _.template($('#alert-template').html());
            this.role = options.role;
            this.content = options.content;
        },

        render: function()
        {
            $(this.el).html(this.template(
                {
                    role: this.role,
                    content: this.content
                }
            ));
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    /**
     * A generic loading bar.
     *
     * @type {*|void}
     */
    var LoadingBarView = CantusAbstractView.extend
    ({
        label: null,
        completion: 0,

        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template = _.template($('#loading-bar-template').html());

            if (options !== undefined)
            {
                if (options.label !== undefined)
                {
                    this.label = String(options.label);
                }
                if (options.completion !== undefined)
                {
                    this.completion = this.setCompletion(options.completion);
                }
            }
        },

        /**
         * Set the completion value.
         *
         * @param completion
         */
        setCompletion: function(completion)
        {
            if (parseInt(completion) < 0)
            {
                this.completion = 0;
            }
            else if (parseInt(completion) > 100)
            {
                this.completion = 100;
            }
            else {
                this.completion = parseInt(completion);
            }
            this.render();
        },

        render: function()
        {
            $(this.el).html(this.template(
                {
                    label: this.label,
                    completion: this.completion
                }
            ));
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    /*
    Page Views
     */

    /**
     * This is the homepage of the website.
     *
     * @type {*|void}
     */
    var IndexPageView = CantusAbstractView.extend
    ({
        el: $('#view-goes-here'),

        events: {
            "click #manuscripts-hero-button" : function()
            {
                app.navigate("/manuscripts/", {trigger: true});
            }
        },

        initialize: function()
        {
            _.bindAll(this, 'render');
            this.template = _.template($('#index-template').html());
        },

        render: function()
        {
            $(this.el).html(this.template());
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    /**
     * This page shows an individual manuscript.  You get a nice diva viewer
     * and you can look through the chant info.
     *
     * @type {*|void}
     */
    var ManuscriptIndividualPageView = CantusAbstractView.extend
    ({
        el: $('#view-goes-here'),

        id: null,
        manuscript: null,
        searchView: null,
        searchNotationView: null,

        // Subviews
        divaView: null,
        folioView: null,

        initialize: function (options) {
            _.bindAll(this, 'render', 'afterFetch', 'updateFolio');
            this.template = _.template($('#manuscript-template').html());
            this.manuscript = new Manuscript(
                    siteUrl + "manuscript/" + this.id + "/");
            // Build the subviews
            this.divaView = new DivaView(
                {
                    siglum: this.manuscript.get("siglum_slug"),
                    folio: options.folio
                }
            );
            this.folioView = new FolioView();
            this.searchView = new SearchView({showManuscriptName: false});
            this.searchNotationView = new SearchNotationView(
                {
                    divaView: this.divaView
                }
            );
            // Render every time the model changes...
            this.listenTo(this.manuscript, 'change', this.afterFetch);
            // Switch page when necessary
            this.listenTo(globalEventHandler, "manuscriptChangeFolio", this.updateFolio);
        },

        remove: function()
        {
            // Remove the subviews
            this.divaView.remove();
            this.searchView.remove();
            this.searchNotationView.remove();
            this.folioView.remove();
            // Deal with the event listeners
            this.stopListening();
            this.undelegateEvents();
            // Nullify the manuscript model
            this.manuscript = null;
            // Nullify the views
            this.divaView = null;
            this.searchView = null;
            this.searchNotationView = null;
            this.folioView = null;
            // Remove from the dom
            this.$el.empty();
        },

        /**
         * 
         * @returns {undefined}
         */
        updateFolio: function()
        {
            var folio = this.divaView.getFolio();
            // Query the folio set at that specific manuscript number
            newUrl =  siteUrl + "folio-set/manuscript/"
                      + this.manuscript.toJSON().id + "/"
                      + folio + "/";
            // Rebuild the folio View
            this.folioView.setUrl(newUrl);
            this.folioView.setCustomNumber(folio);
            this.folioView.update();
            globalEventHandler.trigger("ChangeFolio", folio);
            globalEventHandler.trigger("SilentUrlUpdate");
        },

        /**
         * Fetch the manuscript's data from the API.
         */
        getData: function()
        {
            this.manuscript.fetch();
        },

        afterFetch: function()
        {
            // Set the search view to only search this manuscript
            this.searchView.setQueryPostScript(' AND manuscript:"'
                + this.manuscript.toJSON().siglum + '"');
            // TODO: Diva is being initialized twice!!!!!!!
            this.divaView.setManuscript(this.manuscript.get("siglum_slug"));
            this.searchNotationView.setManuscript(this.manuscript.get("siglum_slug"));
            this.render();
        },

        render: function()
        {
            $(this.el).html(this.template({
                manuscript: this.manuscript.toJSON()
            }));

            // Render subviews
            if (this.divaView !== undefined) {
                this.assign(this.divaView, '.diva-wrapper');
            }
            this.renderFolioView();
            this.assign(this.searchView, '#manuscript-search');
            this.assign(this.searchNotationView, '#search-notation');
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        },

        renderFolioView: function()
        {
            if (this.divaView !== undefined) {
                this.assign(this.folioView, '#folio');
            }
        }

    });

    /**
     * This page is a big list of manuscripts.
     *
     * @type {*|void}
     */
    var ManuscriptsPageView = CantusAbstractView.extend
    ({
        el: $('#view-goes-here'),

        loaded: false,

        //Subviews
        manuscriptCollectionView: null,
        loadingAlertView: null,

        initialize: function()
        {
            _.bindAll(this, "render", "update", "afterFetch");
            this.template= _.template($('#manuscripts-page-template').html());
            //Subviews
            this.manuscriptCollectionView = new ManuscriptCollectionView(
                {url: siteUrl + "manuscripts/"});
            this.loadingAlertView = new AlertView({content:"Loading manuscripts...", role:"info"});
            // Listen for changes
            this.listenTo(this.manuscriptCollectionView.collection, 'sync', this.afterFetch);
        },

        update: function()
        {
            this.manuscriptCollectionView.update();
        },

        afterFetch: function()
        {
            // The manuscripts are loaded, so we don't need the loading bar...
            this.loaded = true;
            this.render();
        },

        render: function()
        {
            $(this.el).html(this.template());
            if (this.loaded)
            {
                this.assign(this.manuscriptCollectionView, '.manuscript-list');
            }
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });

    /**
     * This page is for searching.
     *
     * @type {*|void}
     */
    var SearchPageView = CantusAbstractView.extend
    ({
        el: $('#view-goes-here'),

        // Subviews
        searchView: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#search-page-template').html());
            // Initialize the subviews
            this.searchView = new SearchView(
                {
                    query: options.query,
                    showManuscriptName: true
                }
            );
        },

        render: function()
        {
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.searchView, '#search');
            globalEventHandler.trigger("renderView");
            return this.trigger('render', this);
        }
    });


    /*
    Routers
     */

    var Workspace = Backbone.Router.extend
    ({
        // The global state model
        globalState: null,
        // Common to all routes
        headerView: null,
        // Only on certain routes
        indexView: null,
        manuscriptsPageView: null,
        manuscriptView: null,
        searchPageView: null,

        routes: {
            "" : "manuscripts",
            "manuscript/:query/?folio=(:folio)&chant=(:chant)": "manuscriptSingle",
            "manuscript/:query/?folio=(:folio)": "manuscriptSingle",
            "manuscript/:query/": "manuscriptSingle",
            "manuscripts/": "manuscripts",
            "search/?q=(:query)": "search",
            "search/": "search",
            '*path': "notFound"
        },

        // We always want the header
        initialize: function()
        {
            this.globalState = new GlobalStateModel();
            // There is always a header!
            this.headerView = new HeaderView({el:".header"});
            this.headerView.render();

            // IndexPageView has no state, so we might as well instantiate it
            this.indexView = new IndexPageView();
            // Same with manuscripts page
            this.manuscriptsPageView = new ManuscriptsPageView();
        },

        index: function()
        {
            this.indexView.render();
        },

        manuscripts: function()
        {
            this.manuscriptsPageView.update();
            this.manuscriptsPageView.render();
        },

        manuscriptSingle: function(query, folio, chant)
        {
            if (this.manuscriptView !== null)
            {
                // We want to make sure that the old view, if it exists, is
                // completely cleared-out.
                this.manuscriptView.divaView.uninitializeDiva();
                this.manuscriptView.remove();
                this.manuscriptView = null;
            }

            this.manuscriptView = new ManuscriptIndividualPageView(
                {
                    id: query,
                    folio: folio
                }
            );
            // Fetch the data
            this.manuscriptView.getData();

            globalEventHandler.trigger("ChangeManuscript", query);
            globalEventHandler.trigger("ChangeChant", chant);
        },

        search: function(query)
        {
            // Delete a search view if it exists
            if (this.searchView !== null && this.searchView !== undefined)
            {
                this.searchView.remove();
                this.searchView = null;
            }

            this.searchView = new SearchPageView({query: query});
            this.searchView.render();
        },

        notFound: function()
        {
            // TODO: Handle 404 somehow
        }
    });

    var app = new Workspace();

    // This gets the router working
    Backbone.history.start({ pushState: true });

})(jQuery);
