(function($){

    /*
    Models
     */

    var CantusAbstractModel = Backbone.Model.extend(
    {
        initialize: function(url)
        {
            this.url = url;
        }
    });

    var Chant = CantusAbstractModel.extend(
    {
        defaults: function()
        {
            return {
                marginalia: "the marginalia",
                folio: "the folio",
                sequence:"the sequence",
                cantus_id: "the cantus id",
                feast: "the feast",
                office: "the office",
                genree: "the genre",
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

    var Concordance = CantusAbstractModel.extend(
    {
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

    var Folio = CantusAbstractModel.extend(
    {
        defaults: function()
        {
            return {
                number: "000",
                manuscript: null,
                chant_count: 0
            }
        }
    });

    var Manuscript = CantusAbstractModel.extend(
    {
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
    var SearchResult = CantusAbstractModel.extend(
    {
        initialize: function(query)
        {
            CantusAbstractModel.__super__.initialize.apply(
                this, "http://localhost:8000/search/?q=" + query);
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
    var CantusAbstractCollection = Backbone.Collection.extend(
    {
        initialize: function(url)
        {
            this.url = url;
        }
    });

    var ChantCollection = CantusAbstractCollection.extend(
    {
        model: Chant
    });

    var ConcordanceCollection = CantusAbstractCollection.extend(
    {
        model: Concordance
    });

    var FolioCollection = CantusAbstractCollection.extend(
    {
        model: Folio
    });

    var ManuscriptCollection = CantusAbstractCollection.extend(
    {
        model: Manuscript
    });


    /*
    Views
    */

    var CantusAbstractView = Backbone.View.extend(
    {
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

    var ChantView = CantusAbstractView.extend(
    {
        chant: null,

        initialize: function(url)
        {
            this.chant = new Chant(url);
        },

        render: function()
        {

        }
    });

    var ManuscriptPageView = CantusAbstractView.extend(
    {
        el: $('#view-goes-here'),

        id: null,
        manuscript: null,
        folioSet: null,
        activeFolioNumber: null,

        // Subviews
        headerView: null,
        divaView: null,

        initialize: function()
        {
            _.bindAll(this, 'render', 'afterFetch');
            this.template= _.template($('#manuscript-template').html());

            console.log("Creating manuscript with id=" + this.id);
            this.manuscript = new Manuscript("http://localhost:8000/manuscript/" + this.id + "/");
            this.folioSet = new FolioCollection();

            // Render every time the model changes...
            this.listenTo(this.manuscript, 'sync', this.afterFetch);

            // Build the subviews
            this.headerView = new HeaderView();
            this.divaView = new DivaView({siglum: this.manuscript.get("siglum_slug")});

            // Render self
//            this.render();
        },

        getData: function()
        {
            this.manuscript.fetch();
            console.log("HomePageView data fetched.");
        },

        afterFetch: function()
        {
            console.log("after manuscript fetch...");
            this.divaView = new DivaView({siglum: this.manuscript.get("siglum_slug")});
            this.render();
        },

        render: function()
        {
            console.log("Rendering");
            $(this.el).html(this.template({
                manuscript: this.manuscript.toJSON()
            }));

            // Render subviews
            this.assign(this.headerView,        '.header');
            if (this.divaView !== undefined)
            this.assign(this.divaView, '#diva-wrapper');

            console.log("Rendering done");
            return this.trigger('render', this);
        },

        /**
         * Assign the active folio to be displayed.
         * @param url
         */
        setActiveFolio: function(url)
        {
            this.activeFolio = new Folio(url);
            this.activeFolio.fetch();
        }
    });

    var FolioView = CantusAbstractView.extend(
    {
        folio: null,

        // Subviews
        chantCollectionView: null,

        initialize: function(url)
        {
            this.folio = new Folio(url);
        },

        render: function()
        {

        }
    });

    var DivaView = CantusAbstractView.extend(
    {
        siglum: null,

        initialize: function(siglum)
        {
            console.log("DivaView initialized.");
            // TODO: Figure out this nonsense
            this.siglum = siglum.siglum;
        },

        render: function()
        {
            siglum = this.siglum;
            console.log(siglum);
            console.log("Rendering Diva View");
            $(document).ready(function() {
                var dv;
                $("#diva-wrapper").diva({
                // $(this.el).diva({
                    enableAutoTitle: false,
                    enableAutoWidth: true,
                    enableAutoHeight: true,
                    enableFilename: false,
                    fixedHeightGrid: false,
                    iipServerURL: "http://localhost:8001/fcgi-bin/iipserver.fcgi",
                    objectData: "/static/" + siglum + ".json",
                    imageDir: "/Users/afogarty/Documents/manuscript-images/processed/"
                        + siglum + "/",
                    onScroll: function ()
                    {
                        // This is the page number
                        console.log(dv.getState()["p"]);

                        // This is the photograph file name
                        // console.log("Just scrolled to: "+ dv.getState()["i"]);
                    },
                    onJump: function ()
                    {
                        console.log("Just jumped to: " );
                    },
                    onDocumentLoaded: function ()
                    {
                        console.log("Document loaded" );
                    }
                });
                var dv = $("#diva-wrapper").data("diva");
//                var dv = $(this.el).data("diva");
            });

            console.log("Done rendering Diva View");
            return this.trigger('render', this);
        }
    });

    var HeaderView = CantusAbstractView.extend(
    {
//        el: $('.header'),
        title: null,

        initialize: function(title)
        {
            this.title = title;
            this.template= _.template($('#header-template').html());
            console.log("HeaderView initialized.");
        },

        render: function()
        {
            $(this.el).html(this.template());
            console.log("HeaderView rendered.");
            return this.trigger('render', this);
        }
    });

    var ManuscriptCollectionView = CantusAbstractView.extend(
    {
        initialize: function(url)
        {
            this.template= _.template($('#manuscript-collection-template').html());

            this.collection = new ManuscriptCollection({url: url});
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

    var ManuscriptsPageView = CantusAbstractView.extend(
    {
        el: $('#view-goes-here'),

        //Subviews
        headerView: null,
        manuscriptCollectionView: null,

        initialize: function()
        {
            _.bindAll(this, 'render', 'afterFetch');
            this.template= _.template($('#manuscripts-template').html());
            this.collection = new ManuscriptCollection("http://localhost:8000/manuscripts/");
            this.listenTo(this.collection, 'sync', this.afterFetch);

            //Subviews
            this.headerView = new HeaderView();
            this.manuscriptCollectionView = new ManuscriptCollectionView()
                .initialize("http://localhost:8000/manuscripts/");
        },

        getData: function()
        {
            this.collection.fetch();
            console.log("ManuscriptCollectionView data fetched.");
        },

        afterFetch: function()
        {
            console.log("ManuscriptCollectionView afterFetch()");
            this.render();
        },

        render: function()
        {
            console.log("About to render ManuscriptCollectionViewtemplate...");
            console.log(this.collection.toJSON());
            $(this.el).html(this.template({
                manuscripts: this.collection.toJSON()
            }));

            this.assign(this.headerView,        '.header');

            console.log("ManuscriptCollectionView template rendered...");
            return this.trigger('render', this);
        }
    });

    var IndexPageView = CantusAbstractView.extend(
    {
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
            console.log("About to render IndexView...");
//            console.log(this.collection.toJSON());
            $(this.el).html(this.template());
            // Render subviews
            this.assign(this.headerView, '.header');

            console.log("IndexView template rendered...");
            return this.trigger('render', this);
        }
    });


    /*
    Routers
     */

    var Workspace = Backbone.Router.extend(
    {
        routes: {
            "" : "index",
            "manuscript/:query/": "manuscript",
            "manuscripts/": "manuscripts",
            '*path': "notFound"
        },

        index: function()
        {
            console.log("Index route.");
            var index = new IndexPageView();
            index.render();
        },

        manuscripts: function()
        {
            console.log("Manuscripts route.");
            var manuscripts = new ManuscriptsPageView();
            // Render initial templates
            manuscripts.render();
            // Fetch the data
            manuscripts.getData();
        },

        manuscript: function(query)
        {
            console.log("Manuscript route.");
            var manuscript = new ManuscriptPageView({ id: query });
            // Render initial templates
            manuscript.render();
            // Fetch the data
            manuscript.getData();
        },

        notFound: function()
        {
            console.log("404 - Backbone route not found!");
        }
    });

    var route = new Workspace();

    // This gets the router working
    Backbone.history.start({ pushState: true });

})(jQuery);