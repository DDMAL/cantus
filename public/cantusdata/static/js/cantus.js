(function($){

    const siteUrl = "http://localhost:8000/";
    const iipImageServerUrl = "http://localhost:8001/";
    const divaImageDirectory = "/Users/afogarty/Documents/manuscript-images/processed/";

    // Global Event Handler for global events
    var globalEventHandler = {};
    _.extend(globalEventHandler, Backbone.Events);


    /*
    Models
     */

    var CantusAbstractModel = Backbone.Model.extend
    ({
        initialize: function(url)
        {
            this.url = url;
//            console.log("Model URL: " + this.url);
//            console.log(this.url);
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
        defaults: function()
        {
            return {
                number: "000",
                manuscript: null,
                chant_count: 0,
                chant_set: []
            }
        }
    });

    var Manuscript = CantusAbstractModel.extend
    ({
        defaults: function()
        {
            return {
                url: "#",
                name: "Test Name",
                siglum: "Test Siglum",
                siglum_slug: "#",
                date: "Tomorrow",
                provenance: "Test provenance",
                description: "This is a nice manuscript...",
                chant_count: 5
            };
        }
    });

    /**
     * This represents a search result.  It is experimental.
     */
    var SearchResult = Backbone.Model.extend
    ({
        initialize: function(pQuery)
        {
            this.setQuery(pQuery);
        },

        setQuery: function(query)
        {
            this.url = siteUrl + "search/?q=" + query;
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
                        // TODO: Have this work with non-numbered folios
                        newElement.url = "/manuscript/" + current.manuscript_id
                            + "/#p2=" + current.folio;
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
            }
        }
    });


    /*
    Collections
     */

    var CantusAbstractCollection = Backbone.Collection.extend
    ({
        initialize: function(url)
        {
            this.url = url;
        },

        defaults: function()
        {
            return []
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
//            view.setElement(this.$(selector)).render();
        }
    });

    var ChantCollectionView = CantusAbstractView.extend
    ({
        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#chant-collection-template').html());
            this.collection = new ChantCollection(options.url);
            this.collection.fetch();
            // TODO: Figure out why this is still rendering multiple times
            this.listenTo(this.collection, 'sync', this.render);
        },

        /**
         * Set the URL of the collection and fetch the data.
         *
         * @param url
         */
        setUrl: function(url)
        {
            this.collection.url = url;
            this.collection.fetch();
        },

        /**
         * Render the collection.
         *
         * @returns {*}
         */
        render: function()
        {
            console.log("Rendering Chant Collection.");
            // Render out the template
            $(this.el).html(this.template(
                {
                    chants: this.collection.toJSON()
                }
            ));
            return this.trigger('render', this);
        }
    });

    var DivaView = CantusAbstractView.extend
    ({
        currentFolioIndex: 0,
        currentFolioName: 0,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'storeFolioIndex');
            this.siglum = options.siglum;
        },

        render: function()
        {
            // It's kind of hacky to doubly-bind the name like this, but I'm
            // not aware of any other way to access storeFolioIndex() from the
            // anonymous function below.
            var storeFolioIndex = this.storeFolioIndex;
            var siglum = this.siglum;
            $(document).ready(function() {
                $("#diva-wrapper").diva({
                // $(this.el).diva({
                    enableAutoTitle: false,
                    enableAutoWidth: true,
                    enableAutoHeight: true,
                    enableFilename: false,
                    fixedHeightGrid: false,
                    iipServerURL: iipImageServerUrl + "fcgi-bin/iipserver.fcgi",
                    objectData: "/static/" + siglum + ".json",
                    imageDir: divaImageDirectory + siglum
                });
                diva.Events.subscribe("VisiblePageDidChange", storeFolioIndex);
            });
            return this.trigger('render', this);
        },

//        currentPage: null,

        storeFolioIndex: function(index, fileName)
        {
            console.log("PAGEDIDLOAD " + fileName);
            if (index != this.currentFolioIndex)
            {
                console.log("INDEX " + index);
//                console.log("GETCURRENT " + )
                this.currentFolioIndex = index;
                this.currentFolioName = fileName;
                globalEventHandler.trigger("manuscriptChangeFolio");
            }
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

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'afterFetch', 'assignChants');

            // This needs to be set by default
            this.setCustomNumber(0);

            this.template= _.template($('#folio-template').html());
            this.model = new Folio(options.url);
            this.model.fetch();
            // Assign the chant list and render when necessary
            this.listenTo(this.model, 'sync', this.afterFetch);
            this.chantCollectionView = new ChantCollectionView({url: "#"});
        },

        update: function()
        {
            this.model.fetch();
        },

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

            console.log("TEEEEEEEEEEEST: " + folio_id);
            // Compose the url
            var composedUrl = siteUrl + "chant-set/folio/" + folio_id + "/";
            console.log("composedUrl: " + composedUrl);
            // Build a new view with the new data
            this.chantCollectionView.setUrl(composedUrl);
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

        render: function()
        {
            $(this.el).html(this.template(
                {number: this.customNumber, model: this.model.toJSON()}
            ));

            if (this.chantCollectionView !== null) {
                this.assign(this.chantCollectionView, '#chant-list');
            }

            return this.trigger('render', this);
        }
    });

    var HeaderView = CantusAbstractView.extend
    ({
        // Subviews
        topMenuView: null,

        initialize: function()
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#header-template').html());

            // Create the TopMenuView with all of its options
            this.topMenuView = new TopMenuView(
                {
                    menuItems: [
                        {
                            name: "Home",
                            url: "/",
                            active: false
                        },
                        {
                            name: "Manuscripts",
                            url: "/manuscripts/",
                            active: false
                        },
                        {
                            name: "Search",
                            url: "/search/",
                            active: false
                        }
                    ]
                }
            )
        },

        render: function()
        {
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.topMenuView, '#top-menu');
            return this.trigger('render', this);
        }
    });

    var TopMenuView = CantusAbstractView.extend
    ({
        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#top-menu-template').html());

            // Menu list items provided
            this.items = options.menuItems;
        },

        render: function()
        {
            $(this.el).html(this.template({items: this.items}));
            return this.trigger('render', this);
        }
    });

    var ManuscriptCollectionView = CantusAbstractView.extend
    ({
        template: null,
        collection: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'update');
            this.template= _.template($('#manuscript-collection-template').html());

            this.collection = new ManuscriptCollection(options.url);
            this.collection.fetch();

            this.listenTo(this.collection, 'sync', this.render);
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
            return this.trigger('render', this);
        }
    });

    var SearchView = CantusAbstractView.extend
    ({
        query: null,

        // Subviews
        searchResultView: null,

        events: {
            // This should call newSearch when the button is clicked
            "click #search-button" : "newSearch",
            "change #search-input" : "newSearch",
            "input #search-input" : "autoNewSearch"
        },

        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#search-template').html());
            // If not supplied, the query is blank
            if (options !== undefined && options.query !== undefined) {
                this.query = options.query;
            } else {
                this.query = "";
            }
            //Date to use for checking timestamps
            this.lastSearchTime = new Date().getTime();
            this.searchResultView = new SearchResultView({query: this.query});
        },

        newSearch: function()
        {
            // Grab the new search query
            var newQuery = encodeURIComponent($('#search-input').val());
            if (newQuery !== this.query) {
                this.query = newQuery;
                // Set the new query and fetch it!
                this.searchResultView.model.setQuery(this.query);
                // This should automatically re-render the results... I think...
                this.searchResultView.model.fetch();
                app.navigate("/search/?q=" + this.query);
                this.lastSearchTime = new Date().getTime();
            }
        },

        autoNewSearch: function()
        {
            if ((new Date().getTime() - this.lastSearchTime) > 100) {
                this.newSearch();
            }
        },

        render: function()
        {
            $(this.el).html(this.template({query: this.query}));
            // Render subviews
            this.assign(this.searchResultView, '#search-result');
            return this.trigger('render', this);
        }
    });

    var SearchResultView = CantusAbstractView.extend
    ({
        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template = _.template($('#search-result-template').html());

            if (options.query !== undefined)
            {
                this.model = new SearchResult(options.query);
            }
            else
            {
                this.model = new SearchResult();
            }

            // Query the search result
            this.model.fetch();
            this.listenTo(this.model, 'sync', this.render);
        },

        render: function()
        {
            // Only render if the model is defined
            if (this.model !== undefined)
            {
                $(this.el).html(this.template({results: this.model.getFormattedData()}));
            }
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

        // Subviews
        headerView: null,

        initialize: function()
        {
            _.bindAll(this, 'render');
            this.template = _.template($('#index-template').html());
            // Initialize the subviews
            this.headerView = new HeaderView();
        },

        render: function()
        {
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.headerView, '.header');
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
        folioCollection: null,
        folioHashSet: null,

        // Subviews
        headerView: null,
        divaView: null,
        folioView: null,

        initialize: function()
        {
            _.bindAll(this, 'render', 'afterFetch', 'updateFolio');
            this.template= _.template($('#manuscript-template').html());
            this.manuscript = new Manuscript(
                siteUrl + "manuscript/" + this.id + "/");
            this.folioHashSet = [];
            // Build the subviews
            this.headerView = new HeaderView();
            this.divaView = new DivaView({siglum: this.manuscript.get("siglum_slug")});

            // TODO: Have the FolioView initialized at the first folio of the book
            this.folioView = new FolioView({url: "#"});
            this.folioView.setCustomNumber(0);

            // Render every time the model changes...
            this.listenTo(this.manuscript, 'change', this.afterFetch);
            // Switch page when necessary
            this.listenTo(globalEventHandler, "manuscriptChangeFolio", this.updateFolio);
        },

        updateFolio: function()
        {
            this.activeFolioName = this.divaView.currentFolioName;

            // Grab the new page index from the diva view
//            this.setUrlFolioIndex(this.divaView.currentFolioIndex);

            // Pull out the folio number from the Diva view
            var splitFolioName = this.activeFolioName.split('.')[0].split('_');
            // Grab the finalmost element before
            var folioNumber = splitFolioName[splitFolioName.length - 1];
            console.log("folioNumber: " + folioNumber);
            console.log(this.manuscript.toJSON());
            // Query the folio set at that specific manuscript number
            newUrl =  siteUrl + "folio-set/manuscript/"
                      + this.manuscript.toJSON().id + "/"
                      + folioNumber + "/";

            console.log("newUrl = " + newUrl);

            // Rebuild the folio View
            this.folioView.model.url = newUrl;
            this.folioView.setCustomNumber(folioNumber);
            this.folioView.update();
            // Render it
            this.renderFolioView();
        },

//        /**
//         * Sets the url to the page index
//         * @param index
//         */
//        setUrlFolioIndex: function(index)
//        {
//            app.navigate("#p2=" + index, {trigger: false, replace: true});
//        },

        getData: function()
        {
            this.manuscript.fetch();
        },

        afterFetch: function()
        {
            hashSet = this.folioHashSet;
            this.divaView = new DivaView({siglum: this.manuscript.get("siglum_slug")});
            this.render();
        },

        render: function()
        {
            $(this.el).html(this.template({
                manuscript: this.manuscript.toJSON()
            }));

            // Render subviews
            this.assign(this.headerView, '.header');

            if (this.divaView !== undefined) {
                this.assign(this.divaView, '#diva-wrapper');
            }
            this.renderFolioView();

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

        //Subviews
        headerView: null,
        manuscriptCollectionView: null,

        initialize: function()
        {
            _.bindAll(this, 'render', 'update');
            this.template= _.template($('#manuscripts-page-template').html());
            //Subviews
            this.headerView = new HeaderView();
            this.manuscriptCollectionView = new ManuscriptCollectionView(
                {url: siteUrl + "manuscripts/"});
            // Listen for changes
            this.listenTo(this.manuscriptCollectionView.collection, 'sync', this.afterFetch);
        },

        update: function()
        {
            this.manuscriptCollectionView.update();
        },

        render: function()
        {
            $(this.el).html(this.template());
            this.assign(this.headerView, '.header');
            this.assign(this.manuscriptCollectionView, '.manuscript-list');
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
        headerView: null,
        searchView: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#search-page-template').html());
            // Initialize the subviews
            this.headerView = new HeaderView();
            this.searchView = new SearchView({query: options.query});
        },

        render: function()
        {
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.headerView, '.header');
            this.assign(this.searchView, '#search');
            return this.trigger('render', this);
        }
    });


    /*
    Routers
     */

    var Workspace = Backbone.Router.extend
    ({
        routes: {
            "" : "index",
            "manuscript/:query/": "manuscriptSingle",
            "manuscripts/": "manuscripts",
            "search/": "search",
            "search/?q=(:query)": "search",
            '*path': "notFound"
        },

        index: function()
        {
            var index = new IndexPageView();
            index.render();
        },

        manuscripts: function()
        {
            var manuscripts = new ManuscriptsPageView();
            // Render initial templates
            manuscripts.render();
            // Fetch the data
            manuscripts.update();
        },

        manuscriptSingle: function(query)
        {
            var manuscript = new ManuscriptIndividualPageView({ id: query });
            // Fetch the data
            manuscript.getData();
        },

        search: function(query)
        {
            var search = new SearchPageView({query: query});
            search.render();
        },

        notFound: function()
        {
            console.log("404 - Backbone route not found!");
        }
    });

    var app = new Workspace();

    // This gets the router working
    Backbone.history.start({ pushState: true });

})(jQuery);