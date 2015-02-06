(function($){
    "use strict";

    /*
    Global Variables
     */

    var SITE_URL = "/neumeeditor/";
    var SITE_SUBFOLDER = "neumeeditor/";
    var STATIC_URL = "/neumeeditor/media/";

    /*
    Boilerplate Code
     */

    // Enable CRSF in sync
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    var oldSync = Backbone.sync;
    Backbone.sync = function(method, model, options){
        options.beforeSend = function(xhr){
            xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        };
        return oldSync(method, model, options);
    };

    /*
    Static functions
     */

    /**
     * Get the absolute url for a given glyph id.
     *
     * @static
     * @param id {int}
     * @returns {string}
     */
    function getAbsoluteGlyphUrl(id)
    {
        return SITE_URL + "glyph/" + String(parseInt(id)) + "/";
    }

    /*
    Router
    */
    var NeumeeditorRouter = Backbone.Marionette.AppRouter.extend({
        /* standard routes can be mixed with appRoutes/Controllers above */
        routes : {
            "neumeeditor/" : "openGlyphList",
            "neumeeditor/glyph/:id/" : "openGlyphEditor"
        },

        openGlyphList: function(){
            console.log("Open Glyph List.");
            // Start the glyph list module
            App.module("GlyphList").start();
        },

        openGlyphEditor: function(id){
            console.log("Open Glyph List.");
            // Start the glyph list module
            App.module("GlyphEdit").start();
            App.module("GlyphEdit").initializeId(id);
        },

        routeToPage: function(url) {
            console.log("url:", url);
            console.log("URL: ", url);
            // var newPageUrl = String(url);
            var newPageUrl = SITE_SUBFOLDER + String(url).replace(/.*\/neumeeditor\//g, "");
            console.log(newPageUrl);
            this.navigate(
                    // Strip site url if need be
                    newPageUrl,
                    {trigger: true}
                );
        }
    });

    /*
    App initialization
     */

    var App = new Backbone.Marionette.Application();
    var AppRouter = new NeumeeditorRouter();

    App.on('initialize:before', function(options)
    {
        // options.anotherThing = true; // Add more data to your options
    });
    App.on('initialize:after', function(options)
    {
        // console.log('Initialization Finished');
    });
    App.on('start', function(options)
    {
        // Get history going
        Backbone.history.start({pushState: true});
    });

    App.addRegions({
        container: "#content",
        navigation: "#navigation"
    });




    /*  
    ------------------------------------------------------
    Models
    ------------------------------------------------------
    */

    var Image = Backbone.Model.extend({
        initialize: function(options)
        {
            if (options !== undefined && options.url !== undefined)
            {
                this.url = String(options.url);
            }
        },

        url: SITE_URL + "images/",

        defaults: {
            image_file: ""
        },

        /**
         * Get the absolute url to the image file.
         *
         * @returns {string}
         */
        getAbsoluteImageFile: function()
        {
            return STATIC_URL + this.get("image_file");
        }
    });

    var Name = Backbone.Model.extend({
        initialize: function(options)
        {
            if (options !== undefined && options.url !== undefined)
            {
                this.url = String(options.url);
            }
        },

        url: SITE_URL + "names/",

        defaults: {
            string: ""
        },

        /**
         * Set the Name's glyph based on the ID int.
         *
         * @param id
         */
        setGlyph: function(id)
        {
            this.set("glyph", getAbsoluteGlyphUrl(id));
        },

        /**
         * Set the model url to its url attribute.
         */
        transferUrl: function()
        {
            this.url = this.get("url");
        }
    });

    var Glyph = Backbone.Model.extend({

        initialize: function(options)
        {
            this.url = String(options.url);
        },

        /**
         * Get a collection containing the Glyph's names.
         *
         * @param attributeName
         * @param CollectionType
         * @param ItemType
         * @returns {CollectionType}
         */
        // getCollection: function(attributeName, CollectionType, ItemType)
        // {
        //     var output = new CollectionType();
        //     var urlList = this.get(String(attributeName));
        //     if (urlList === undefined) {
        //         // This prevents crashing if the list is undefined.
        //         return undefined;
        //     }
        //     // If we don't encapsulate sort() in a function then we get errors on load.
        //     var sortOutput = function() {output.sort();};

        //     var newModel;
        //     for (var i = 0; i < urlList.length; i++)
        //     {
        //         newModel = new ItemType({url: String(urlList[i])});
        //         output.add(newModel);
        //         newModel.fetch({success: sortOutput});
        //     }
        //     return output;
        // },
        getCollection: function(attributeName, CollectionType, ItemType)
        {
            var collectionAttributes = this.get(String(attributeName));
            var collection = new CollectionType();
            collection.add(collectionAttributes);
            return collection;
        },

        defaults: {
            id: 0,
            short_code: "",
            comments: ""
        }
    });


    /*  
    ------------------------------------------------------
    Collections
    ------------------------------------------------------
    */

    var NameCollection = Backbone.Collection.extend({
        model: Name,

        comparator: function(name)
        {
            // Newest names first
            return 0 - parseInt(name.get("id"));
        }
    });

    var ImageCollection = Backbone.Collection.extend({
        model: Image,

        comparator: function(image)
        {
            // Newest names first
            return 0 - parseInt(image.get("id"));
        }
    });

    var GlyphCollection = Backbone.Collection.extend({
        model: Glyph,

        initialize: function(options)
        {
            this.url = String(options.url);
        },

        comparator: function(image)
        {
            // Newest names first
            return 0 - parseInt(image.get("id"));
        }        
    });


    App.module("MainMenu", function(MainMenu, App, Backbone, Marionette, $, _) {
        this.startWithParent = true;

        /**
         * A generic link
         */
        var Link = Backbone.Model.extend({
            defaults: {
                url: "#",
                text: "Link"
            }
        });

        /** 
         * A link on the main menu.
         */
        var SingleMainMenuLinkView = Backbone.Marionette.ItemView.extend({
            template: "#single-main-menu-link-template",
            tagName: "li",

            events: {
                "click a": "goToUrl"
            },

            goToUrl: function(event) {
                console.log(event);
                event.preventDefault();
                AppRouter.routeToPage(event.target.href);
            }
        });

        /**
         * The main menu.
         */
        var MainMenuView = Backbone.Marionette.CompositeView.extend({
            childView: SingleMainMenuLinkView,
            childViewContainer: ".navbar-left",
            template: "#main-menu-template"
        });

        /*
        Execution Code
        */
        var menuLinks = new Backbone.Collection();
        menuLinks.add(new Link().set({url:SITE_URL + "", text: "List"}));
        // menuLinks.add(new Link());
        // menuLinks.add(new Link());
        var menu = new MainMenuView({collection: menuLinks});
        App.navigation.show(menu);
    });

    App.module("Authentication", function(Authentication, App, Backbone, Marionette, $, _){
        this.startWithParent = false;
    });

    App.module("GlyphList", function(GlyphList, App, Backbone, Marionette, $, _){
        this.startWithParent = false;

        /*
        Item Views
        */

        var ImageView = Backbone.Marionette.ItemView.extend({
            template: "#single-image-template",

            tagName: "li",

            serializeData: function()
            {
                return {
                    "image_file": this.model.getAbsoluteImageFile(),
                    // "image_file_absolute": this.model.getAbsoluteImageFile()
                };
            }
        });

        var NameView = Backbone.Marionette.ItemView.extend({
            template: "#single-name-template",

            tagName: "li"
        });

        var NameCollectionView = Backbone.Marionette.CollectionView.extend({
            childView: NameView,

            tagName: "ul"
        });

        var ImageCollectionView = Backbone.Marionette.CollectionView.extend({
            childView: ImageView,

            tagName: "ul"
        });

        var GlyphView = Backbone.Marionette.LayoutView.extend({
            template: "#glyph-template",
            tagName: "tr",

            regions: {
                names: ".glyph-name-list",
                images: ".glyph-image-list"
            },

            events: {
                "click .edit-button": "goToEdit"
            },

            goToEdit: function(event) {
                console.log(event);
                event.preventDefault();
                AppRouter.routeToPage(this.model.get("url"));
            },

            onRender: function() {
                var nameCollection = this.model.getCollection("name_set", NameCollection, Name);
                var imageCollection;
                try {
                    imageCollection = this.model.getCollection("image_set", ImageCollection, Image);
                }
                catch(ReferenceError) {
                    // Just make a blank collection
                    imageCollection = new ImageCollection();
                }
                this.names.show(new NameCollectionView({
                    collection: nameCollection
                }));
                this.images.show(new ImageCollectionView({
                    collection: imageCollection
                }));                       
            }
        });

        var GlyphCompositeView = Backbone.Marionette.CompositeView.extend({
            childView: GlyphView,

            childViewContainer: "tbody",
            template: "#glyph-collection-template"
        });

        /*  
        ------------------------------------------------------
        Execution Code
        ------------------------------------------------------
        */

        this.start = function()
        {
            var glyphCollection = new GlyphCollection({url: "/neumeeditor/glyphs/"});

            // var glyph = new GlyphListLayoutView({model: glyph});
            var glyphCompositeView = new GlyphCompositeView({collection: glyphCollection});


            App.container.show(glyphCompositeView);

            console.log("Starting...");
            glyphCollection.fetch();
        };
    });

    App.module("GlyphEdit", function(GlyphEdit, App, Backbone, Marionette, $, _){
        this.startWithParent = false;

        /*  
        ------------------------------------------------------
        Views
        ------------------------------------------------------
        */

        /*
        Item Views
         */

        var EditSingleImageView = Backbone.Marionette.ItemView.extend({
            tagName: "div",

            template: _.template($('#edit-single-image-template').html()),

            modelEvents: {
                "change": "render"
            },

            events: {
                "click button[name='delete']": "destroyModel"
            },

            serializeData: function()
            {
                return {
                    "image_file": this.model.getAbsoluteImageFile(),
                    // "image_file_absolute": this.model.getAbsoluteImageFile()
                };
            },

            destroyModel: function()
            {
                console.log("Delete name.");
                event.preventDefault();
                this.model.destroy();
                return this.trigger("destroy");
            }
        });

        /**
         * View for editing a single name object.
         */
        var EditSingleNameView = Backbone.Marionette.ItemView.extend({

            tagName: "form",

            template: _.template($('#edit-single-name-template').html()),

            modelEvents: {
                "change": "render"
            },

            events: {
                "submit": "submitModel",
                "click button[name='delete']": "destroyModel"
            },

            ui: {
                statusDiv: ".status-message"
            },

            submitModel: function(event)
            {
                // Prevent default functionality
                event.preventDefault();
                // Grab values from the form fields
                this.model.set({
                    string: String(this.$("input[name='string']").val())
                });
                var that = this;
                this.model.save(null,
                    {
                        success: function() {
                            console.log("Success.");
                            // console.log(that.ui.statusDiv);
                            that.ui.statusDiv.html("<p>Name saved successfully.</p>");
                            that.ui.statusDiv.find("p").fadeOut(2500);
                            return that.trigger("submit");
                        },
                        error: function() {
                            that.ui.statusDiv.html("<p>Error saving name.<p>");
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        }
                    }
                );
            },

            destroyModel: function()
            {
                console.log("Delete name.");
                event.preventDefault();
                this.model.destroy();
                return this.trigger("destroy");
            }
        });

        var CreateImagesView = Backbone.Marionette.ItemView.extend({
            createdCollection: undefined,
            childView: CreateSingleNameView,
            childViewContainer: ".name-list",
            template: "#upload-image-template",

            initialize: function(options)
            {
                if(options)
                {
                    if (options.createdCollection)
                    {
                        this.createdCollection = options.createdCollection;
                    }
                    if (options.glyphId)
                    {
                        this.glyphId = getAbsoluteGlyphUrl(options.glyphId);
                        console.log("DECLARING GLYPH ID: ", this);
                    }
                }
            },

            childEvents: {
                "submit": "save"
            },

            ui: {
                "dropzone": ".dropzone"
            },

            save: function(child)
            {
                console.log("SAVE CALLBACK:");
            },

            onRender: function()
            {
                console.log("DROPZONE DIV:");
                console.log(this.ui.dropzone);
                console.log("Uploader render.");
                console.log(this.glyphId);
                console.log(this.ui.dropzone.selector);
                console.log(this.ui.dropzone);
                this.ui.dropzone.dropzone(
                // this.dropzone = new Dropzone(this.ui.dropzone.selector,
                    {
                        url: SITE_URL + "images/",
                        autoProcessQueue: true,
                        paramName: "image_file",
                        acceptedFiles: "image/*",
                        headers: {
                            // We need to include the CSRF token again
                            "X-CSRFToken": csrftoken
                        },
                        params: {
                            glyph: this.glyphId
                        }
                    }
                );
                this.ui.dropzone.on("error", function(error) { console.log(error); });
                var that = this;
                this.listenTo(this.ui.dropzone, "success",
                    function(file, attributes)
                    {
                        console.log("Creating image model...", that);
                        // console.log(attributes);
                        // console.log(file);
                        var newModel = new Image({url: attributes.url});
                        newModel.set(attributes);
                        // console.log("childviewcontainer: ", that.childViewContainer);
                        newModel.set("glyph", that.glyphId);
                        // console.log(that.createdCollection);
                        that.createdCollection.add(newModel);
                        newModel.save();
                        // console.log(newModel);
                    }
                );
            }
        });

        var CreateSingleNameView = EditSingleNameView.extend({
            template: _.template($('#create-single-name-template').html())
        });

        /*
        Composite Views
        */

        var CreateNamesView = Backbone.Marionette.CompositeView.extend({

            initialize: function(options)
            {
                var emptyName = new Name();

                if(options)
                {
                    if (options.createdCollection)
                    {
                        this.createdCollection = options.createdCollection;
                    }
                    if (options.glyphId)
                    {
                        emptyName.setGlyph(parseInt(options.glyphId));
                    }
                }
                this.collection = new NameCollection();
                this.collection.add(emptyName);
            },

            childView: CreateSingleNameView,

            childViewContainer: ".name-list",
            template: "#create-name-collection-template",

            childEvents: {
                "submit": "save"
            },

            save: function(child)
            {
                console.log("SAVE CALLBACK:");
                // Remove model from this collection
                // console.log(child.model);
                // Set the new URL
                child.model.transferUrl();
                this.createdCollection.add(child.model);
                this.collection.remove(child.model);
                this.collection.add(new Name());
            }
        });

        var EditNamesView = Backbone.Marionette.CompositeView.extend({
            childView: EditSingleNameView,

            childViewContainer: ".name-list",
            template: "#edit-name-collection-template"
        });

        var EditImagesView = Backbone.Marionette.CompositeView.extend({
            childView: EditSingleImageView,

            childViewContainer: ".images",
            template: "#edit-image-collection-template"
        });

        var EditSingleGlyphView = Backbone.Marionette.CompositeView.extend({
            tagName: "li",
            template: _.template("#edit-single-glyph-template")
        });


        /*
        Layout Views
        */

        var AppLayoutView = Backbone.Marionette.LayoutView.extend({
            template: "#edit-glyph-template",

            /*
            These regions correspond to template areas. They will be populated with
            sub views.
            */
            regions: {
                namesArea: ".names-area",
                nameCreateArea: ".name-create-area",
                imageUploadArea: ".image-upload-area",
                imagesEditArea: ".images-area",
                glyphPropertiesArea: ".glyph-properties-area"
            },

            modelEvents: {
                "change": "onChange"
            },

            events: {
                "click button[name='save-properties']": "saveProperties"
            },

            ui: {
                commentsBox: ".comments-box",
                statusDiv: ".property-status-message"
            },

            initialize: function()
            {
                this.loadNamesAndImages();
            },

            saveProperties: function(event)
            {
                // Prevent default functionality
                event.preventDefault();
                var that = this;
                console.log(this.model.toJSON());
                this.model.save(
                    {
                        comments: String(this.ui.commentsBox.val())
                    },
                    {
                        success: function() {
                            console.log("Success.");
                            that.ui.statusDiv.html("<p>Properties updated successfully.</p>");
                            that.ui.statusDiv.find("p").fadeOut(2500);
                            return that.trigger("submit");
                        },
                        error: function(test1, test2, test3) {
                            console.log(that.model.toJSON());
                            console.log(test1, test2, test3);
                            that.ui.statusDiv.html("<p>Error saving.<p>");
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        }
                    }
                );
            },

            onChange: function()
            {
                this.loadNamesAndImages();
                this.render();
            },

            loadNamesAndImages: function()
            {
                this.glyphNames = glyph.getCollection("name_set", NameCollection, Name);
                this.glyphImages = glyph.getCollection("image_set", ImageCollection, Image);
            },

            onShow: function()
            {
                this.namesArea.show(new EditNamesView(
                    {collection: this.glyphNames}
                ));

                this.nameCreateArea.show(
                    new CreateNamesView({
                        glyphId: glyph.get("id"),
                        createdCollection: this.glyphNames
                    })
                );

                this.imagesEditArea.show(
                    new EditImagesView({
                        collection: this.glyphImages
                    })
                );

                this.imageUploadArea.show(
                    new CreateImagesView({
                        glyphId: this.model.get("id"),
                        createdCollection: this.glyphImages
                    })
                );
            },

            onRender: function()
            {
                this.onShow();
            }

        });

        /*  
        ------------------------------------------------------
        Execution Code
        ------------------------------------------------------
        */

        var glyphId = 1;

        var glyph = new Glyph({
            url: "/neumeeditor/glyph/" + glyphId + "/"
        });

        var editor;

        this.start = function() {
            editor = new AppLayoutView({model: glyph});   
        };
        
        this.initializeId = function(id)
        {
            glyphId = parseInt(id);
            glyph.url = "/neumeeditor/glyph/" + glyphId + "/";  

            // Render the LayoutView
            App.container.show(editor);

            console.log("Starting...");
            glyph.fetch({success: function(){

                // console.log(editor.model);


                // console.log(glyphNames);

            }});
        };


    });
    console.log("start app");
    App.start();

})(jQuery);
