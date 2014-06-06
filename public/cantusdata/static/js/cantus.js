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
        defaults: function()
        {
            return {
                marginalia: "the marginalia",
                folio: "the folio",
                sequence:"the sequence",
                cantus_id: "the cantus id",
                feast: "the feast",
                office: "the office",
                genre: "the genre",
                lit_position: "the lit position",
                mode: "the mode",
                differentia: "the differentia",
                finalis: "the finalis",
                incipit: "the incipit",
                full_text: "Quite a nice chant!",
                concordances: [],
                volpiano: "the volpiano",
                manuscript: "the manuscript"
            }
        }
    });

    var Concordance = CantusAbstractModel.extend
    ({
        defaults: function()
        {
            return {
                letter_code: "ZZZ",
                institution_city: "Montreal",
                instutition_name: "DDMAL",
                library_manuscript_name: "No Name",
                date: "Right now",
                location: "Montreal",
                rism_code: "ABC1234"
            }
        }
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
                chant_count: 5,
                folio_set: [],
                chant_set: []
            };
        },

        /**
         * Turn the folio set into a collection
         */
        getFolioCollection: function() {
            var output = ConcordanceCollection();
            output.reset(this.folio_set);
            return output;
        },

        /**
         * Turn the folio set into a collection
         */
        getChantCollection: function() {
            var output = ChantCollection();
            output.reset(this.chant_set);
            return output;
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
//            console.log("Constructing search result for query:");
//            console.log(query);
            this.url = siteUrl + "search/?q=" + query;
//            console.log(this.url);
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
                // Build the url
                newElement.url = "/" + newElement.model
                    + "/" + current.item_id + "/";
                newElement.name = current.Name;

                // Figure out what the name is based on the model in question
                switch(newElement.model)
                {
                    case "manuscript":
                        newElement.name = current.Name;
                        break;

                    case "chant":
                        newElement.name = current.Incipit;
                        break;

                    case "concordance":
                        newElement.name = current.Name;
                        break;

                    case "folio":
                        newElement.name = current.Name;
                        break;
                }

                output.push(newElement);
            });
//            console.log("search output:");
//            console.log(output);
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
//            console.log("Collection URL: " + this.url);
//            console.log(this.url);
        },

        addUrlList: function(list)
        {
            var newModels = [];

            for (var i = 0; i < list.length; i++)
            {
                newModels.push(new this.model(list[i]));
            }

            // Gotta fetch 'em all!
            for (var j = 0; j < newModels.length; j++)
            {
                // Send out an alert once the last one has been fetched
                theCollection = this;
                if (j === (newModels.length - 1)) {
                   newModels[j].fetch({
                       success: function() {
//                           console.log("Triggered addedUrlList");
                           theCollection.trigger("addedUrlList");
                       }
                   });
                } else {
                    newModels[j].fetch();
                }
            }

            this.push(newModels);
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
            // If a set of chants is supplied, use it!
            if (options !== undefined)
            {
                if (options.collection !== undefined)
                {
                    this.collection = new ChantCollection(options.collection);
                }
                else if (options.url !== undefined)
                {
                    this.collection = new ChantCollection(options.url);
                }
            } else {
                this.collection = new ChantCollection();
            }

            // This might have to render several times...
            this.listenTo(this.collection, 'addedUrlList', this.render);
        },

        render: function()
        {
//            console.log("ChantCollectionView RENDER METHOD");
//            console.log(this.collection.toJSON());
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
        lastFolioChangeTime: 0,

        initialize: function(options)
        {
//            console.log("DivaView initialized.");
//            console.log("Diva Siglum: " + options.siglum);
            _.bindAll(this, 'render', 'storeFolioIndex');
            this.siglum = options.siglum;
        },

        render: function()
        {
            // It's kind of hacky to doubly-bind the name like this, but I'm
            // not aware of any other way to access storeFolioIndex() from the
            // anonymous function below.
            storeFolioIndex = this.storeFolioIndex;
            siglum = this.siglum;
//            console.log(siglum);
//            console.log("Rendering Diva View");
            $(document).ready(function() {
                var dv;
                $("#diva-wrapper").diva({
                // $(this.el).diva({
                    enableAutoTitle: false,
                    enableAutoWidth: true,
                    enableAutoHeight: true,
                    enableFilename: false,
                    fixedHeightGrid: false,
                    iipServerURL: iipImageServerUrl + "fcgi-bin/iipserver.fcgi",
                    objectData: "/static/" + siglum + ".json",
                    imageDir: divaImageDirectory + siglum + "/",
                    onScroll: function ()
                    {
                        // This is the page number
                        storeFolioIndex(dv.getState()["p"]);
                    },
                    onJump: function ()
                    {
                        storeFolioIndex(dv.getState()["p"]);
                    },
                    onDocumentLoaded: function ()
                    {
//                        console.log("Document loaded" );
                    }
                });
                var dv = $("#diva-wrapper").data("diva");
//                var dv = $(this.el).data("diva");
            });
//            console.log("Done rendering Diva View");
            return this.trigger('render', this);
        },

        storeFolioIndex: function(index)
        {
            if (index != this.currentFolioIndex)
            {
//                console.log("TRIGGERING MANUSCRIPTCHANGEFOLIO");
//                if ((new Date().getTime() - this.lastFolioChangeTime) > 1000)
//                {

                    this.currentFolioIndex = index;
                    this.lastFolioChangeTime = new Date().getTime();
                    globalEventHandler.trigger("manuscriptChangeFolio", index);
//                }
            }
        }
    });

    var FolioView = CantusAbstractView.extend
    ({
        // Subviews
        chantCollectionView: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'afterFetch', 'assignChants');
            this.template= _.template($('#folio-template').html());

//            console.log("Initializing Folio: " + options.url);
            this.model = new Folio(options.url);
            this.model.fetch();

//            console.log("New Folio model:");
//            console.log(this.model.toJSON());

            // Assign the chant list and render when necessary
            this.listenTo(this.model, 'sync', this.afterFetch);
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
//            console.log("assignChants");
//            console.log(this.model.toJSON().chant_set);
            this.chantCollectionView = new ChantCollectionView();

            // Add all of the chants
            this.chantCollectionView.collection.addUrlList(this.model.toJSON().chant_set);
//            console.log(this.chantCollectionView.collection);

            this.render();
        },

        render: function()
        {
            $(this.el).html(this.template(this.model.toJSON()));

            if (this.chantCollectionView !== null) {
//                console.log("Rendering ChantCollectionView");
                this.assign(this.chantCollectionView, '#chant-list');
            }

            return this.trigger('render', this);
        }
    });

    var HeaderView = CantusAbstractView.extend
    ({
        // Subviews
        topMenuView: null,

        initialize: function(options)
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

//            console.log("HeaderView constructed.");
        },

        render: function()
        {
            $(this.el).html(this.template());
//            console.log("HeaderView rendered.");

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
//            console.log("Rendering top menu.");
//            console.log(this.items);
            $(this.el).html(this.template({items: this.items}));
            return this.trigger('render', this);
        }
    })

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

//            console.log("TEST:::: " + this.query);
            this.searchResultView = new SearchResultView({query: this.query});
        },

        newSearch: function()
        {
            // Grab the new search query
            var newQuery = encodeURIComponent($('#search-input').val());

            if (newQuery !== this.query) {
                this.query = newQuery;
//                console.log("NewQuery = " + this.query);
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
            // Only update every 1 second
//            console.log(new Date().getTime());
//            console.log(this.lastSearchTime);
            if ((new Date().getTime() - this.lastSearchTime) > 100) {
                // It's been a second, so do the search
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
            this.template= _.template($('#search-result-template').html());

//            console.log("Constructing search results for q=" + options.query);

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
            if (this.model !== undefined)
            {
                // Only render if the model is defined
                console.log("Rendering search result view.");
//                console.log(this.model.toJSON());
                $(this.el).html(this.template({results: this.model.getFormattedData()}));
            }
            else
            {
                console.log("No search result defined, so not rendering.");
            }
            return this.trigger('render', this);
        }
    })

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
            this.template= _.template($('#index-template').html());

            // Initialize the subviews
            this.headerView = new HeaderView();
        },

        render: function()
        {
//            console.log("About to render IndexView...");
//            console.log(this.collection.toJSON());
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.headerView, '.header');

//            console.log("IndexView template rendered...");
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
        folioSet: null,

        // Subviews
        headerView: null,
        divaView: null,
        folioView: null,

        initialize: function(options)
        {
            _.bindAll(this, 'render', 'afterFetch', 'updateFolio');
            this.template= _.template($('#manuscript-template').html());

//            console.log("Creating manuscript with id=" + this.id);
            this.manuscript = new Manuscript(
                siteUrl + "manuscript/" + this.id + "/");
//            console.log("TEST MANUSCRIPT INITIALIZATION:");
//            console.log(this.manuscript);

            // Build the subviews
            this.headerView = new HeaderView();
//            console.log("Siglum Slug: " + this.manuscript.get("siglum_slug"));
//            console.log(this.manuscript.get("siglum_slug"));
            this.divaView = new DivaView({siglum: this.manuscript.get("siglum_slug")});
            this.folioView = new FolioView({url: siteUrl + "folio/" + 551 + "/"});

            // Render every time the model changes...
            this.listenTo(this.manuscript, 'sync', this.afterFetch);
            // Switch page when necessary
            this.listenTo(globalEventHandler, "manuscriptChangeFolio", this.updateFolio);
        },

        updateFolio: function()
        {
            // Grab the new page index from the diva view
            this.activeFolioIndex = this.divaView.currentFolioIndex;
//            console.log("setFolio to " + this.activeFolioIndex);
//            console.log(this.manuscript.toJSON());
            // Get the proper url based on the index
            var newUrl = this.manuscript.toJSON().folio_set[this.activeFolioIndex];
            // Rebuild the folio View
            this.folioView = new FolioView({url: newUrl});
            // Render it
            this.renderFolioView();
        },

        getData: function()
        {
            this.manuscript.fetch();
//            console.log("HomePageView data fetched.");
        },

        afterFetch: function()
        {
//            console.log("after manuscript fetch...");
            this.divaView = new DivaView({siglum: this.manuscript.get("siglum_slug")});
            this.render();
        },

        render: function()
        {
//            console.log("Rendering");
            $(this.el).html(this.template({
                manuscript: this.manuscript.toJSON()
            }));

            // Render subviews
            this.assign(this.headerView,        '.header');

            if (this.divaView !== undefined) {
                this.assign(this.divaView, '#diva-wrapper');
            }
            this.renderFolioView();

//            console.log("Rendering done");
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
//            console.log("About to render ManuscriptCollectionViewtemplate...");
            $(this.el).html(this.template());

            this.assign(this.headerView, '.header');
            this.assign(this.manuscriptCollectionView, '.manuscript-list');

//            console.log("ManuscriptCollectionView template rendered...");
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
//            console.log("About to render SearchPageView...");
            $(this.el).html(this.template());

            // Render subviews
            this.assign(this.headerView, '.header');
            this.assign(this.searchView, '#search');

//            console.log("SearchPageView template rendered...");
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
//            console.log("Index route.");
            var index = new IndexPageView();
            index.render();
        },

        manuscripts: function()
        {
//            console.log("Manuscripts route.");
            var manuscripts = new ManuscriptsPageView();
            // Render initial templates
            manuscripts.render();
            // Fetch the data
            manuscripts.update();
        },

        manuscriptSingle: function(query)
        {
//            console.log("Manuscript route.");
            var manuscript = new ManuscriptIndividualPageView({ id: query });
            // Render initial templates
            manuscript.render();
            // Fetch the data
            manuscript.getData();
        },

        search: function(query)
        {
//            console.log("Search route.");
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