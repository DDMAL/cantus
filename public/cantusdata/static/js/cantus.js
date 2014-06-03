(function($){

    /*
    Models
     */

    var Chant = Backbone.Model.extend({
//        id: 0,
//        url: 'http://localhost:8000/chant/' + this.id,

        initialize: function(url)
        {
            this.url = url;
//            this.id = id;
        },

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

    var Concordance = Backbone.Model.extend({
//        id: 0,
//        url: 'http://localhost:8000/concordance/' + this.id,

        initialize: function(url)
        {
            this.url = url;
//            this.id = id;
        },

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

    var Folio = Backbone.Model.extend({
//        id: 0,
//        url: 'http://localhost:8000/folio/' + this.id,

        initialize: function(url)
        {
            this.url = url;
//            this.id = id;
        },

        defaults: function()
        {
            return {
                number: "000",
                manuscript: null,
                chant_count: 0
            }
        }
    });

    var Manuscript = Backbone.Model.extend(
    {
        initialize: function(url)
        {
            this.url = url;
//            this.url = 'http://localhost:8000/manuscript/' + id + "/";
        },

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


    /*
    Collections
     */

    var ChantCollection = Backbone.Collection.extend({
        model: Chant,
        url: 'http://localhost:8000/chants/'
    })

    var ConcordanceCollection = Backbone.Collection.extend({
        model: Concordance,
        url: 'http://localhost:8000/concordances/'
    })

    var FolioCollection = Backbone.Collection.extend({
        model: Folio,
        url: 'http://localhost:8000/folios/'
    })

    var ManuscriptCollection = Backbone.Collection.extend(
    {
        model: Manuscript,
        url: 'http://localhost:8000/manuscripts/'
    });


    /*
    Views
    */

    var ManuscriptView = Backbone.View.extend(
    {
        el: $('#view-goes-here'),

        id: null,
        manuscript: null,
        folioSet: null,
        activeFolio: null,

        initialize: function()
        {
            _.bindAll(this, 'render', 'afterFetch');
            this.template= _.template($('#manuscript-template').html());
            console.log("Creating manuscript with id=" + this.id);
            this.manuscript = new Manuscript("http://localhost:8000/manuscript/" + this.id + "/");
            this.folioSet = new FolioCollection();
            // Render every time the model changes...
            this.listenTo(this.manuscript, 'sync', this.afterFetch);
            // Render self
            this.render();
        },

        getData: function()
        {
            this.manuscript.fetch();
            console.log("HomePageView data fetched.");
        },

        afterFetch: function()
        {
            console.log("after fetch...");
//            this.folioSet.reset(this.manuscript.folio_set.toJSON());
            this.render();
        },

        render: function()
        {
            console.log("Rendering");
//            console.log(this.manuscript.toJSON());
            $(this.el).html(this.template({
                manuscript: this.manuscript.toJSON()
            }));
            this.renderDiva();
            console.log("Rendering done");
            return this;
        },

        /**
         * Assign the active folio to be displayed.
         * @param url
         */
        setActiveFolio: function(url)
        {
            this.activeFolio = new Folio(url);
            this.activeFolio.fetch();
        },

        /**
         * This function currently doesn't work...
         */
        renderDiva: function() {
            siglum = this.manuscript.get("siglum_slug");
            console.log("Rendering Diva View");
            $(document).ready(function() {
                var dv;
                $("#diva-wrapper").diva({
                    enableAutoTitle: false,
                    enableAutoWidth: true,
                    enableAutoHeight: true,
                    fixedHeightGrid: false,
                    iipServerURL: "http://localhost:8001/fcgi-bin/iipserver.fcgi",
                    objectData: "/static/" + siglum + ".json",
                    imageDir: "/Users/afogarty/Documents/manuscript-images/processed/"
                        + siglum + "/",
                    onScroll: function ()
                    {
                        console.log("Just scrolled to: "+ dv.getState()["i"]);
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
            });

            console.log("Done rendering Diva View");
        }
    });

//    var FolioCollectionView = Backbone.View.extend(
//    {
//        el: $('body'),
//
//        initialize: function()
//        {
//            _.bindAll(this, 'render');
//            this.template= _.template($('#folios-template').html()),
//            this.collection = new FolioCollection();
//            this.listenTo(this.collection, 'change', this.render());
//        },
//
//        getData: function()
//        {
//            this.collection.fetch();
//            console.log("FolioCollectionView data fetched.");
//        },
//
//        render: function()
//        {
//            console.log("About to render HomePageView template...");
//            $(this.el).html(this.template({
//                manuscripts: this.collection.toJSON()
//            }));
//            console.log(this.collection.toJSON());
//            console.log("HomePageView template rendered...");
//            return this;
//        },
//
//        replaceFolios: function(newFolioCollection)
//        {
//            this.collection = newFolioCollection;
//            this.getData();
//        }
//    });


    var ManuscriptCollectionView = Backbone.View.extend(
    {
        el: $('#view-goes-here'),

        initialize: function()
        {
            _.bindAll(this, 'render', 'afterFetch');
            this.template= _.template($('#manuscripts-template').html());
            this.collection = new ManuscriptCollection();
            this.listenTo(this.collection, 'sync', this.afterFetch);
//            this.listenTo(this.collection, 'fetchComplete', this.afterFetch);
        },

        getData: function()
        {
            //this.collection.fetch({
                    //success: function(collection){
                    // This code block will be triggered only after receiving the data.
                    //console.log(collection.toJSON());
                    //this.trigger('fetchComplete');
                //}
            //});
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
            console.log("ManuscriptCollectionView template rendered...");
            return this;
        }
    });

    var IndexView = Backbone.View.extend({

        el: $('#view-goes-here'),

        initialize: function()
        {
            _.bindAll(this, 'render');
            this.template= _.template($('#index-template').html());
        },

        render: function()
        {
            console.log("About to render IndexView...");
//            console.log(this.collection.toJSON());
            $(this.el).html(this.template());
            console.log("IndexView template rendered...");
            return this;
        }
    });


    var Workspace = Backbone.Router.extend({

        routes: {
            "" : "index",
            "manuscript/:query/": "manuscript",
            "manuscripts/": "manuscripts",
            '*path': "notFound"
        },

        index: function()
        {
            console.log("Index route.");
            var app = new IndexView();
            app.render();
        },

        manuscripts: function()
        {
            console.log("Manuscripts route.");
            var app = new ManuscriptCollectionView();
            // Render initial templates
            app.render();
            // Fetch the data
            app.getData();
        },

        manuscript: function(query)
        {
            console.log("Manuscript route.");
            console.log(query);
            var app = new ManuscriptView({ id: query });
            // Render initial templates
            app.render();
            // Fetch the data
            app.getData();
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