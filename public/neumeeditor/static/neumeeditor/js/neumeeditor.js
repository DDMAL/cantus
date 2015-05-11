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
            "neumeeditor/glyph/:id/" : "openGlyphEditor",
            "neumeeditor/nomenclatures/" : "openNomenclatureList"
        },

        openGlyphList: function()
        {
            // Start the glyph list module
            App.module("GlyphList").start();
        },

        openGlyphEditor: function(id)
        {
            // Start the individual glyph editor
            App.module("GlyphEdit").start();
            App.module("GlyphEdit").initializeId(id);
        },

        openNomenclatureList: function()
        {
            // Start the nomenclature list module
            App.module("NomenclatureList").start();
        },

        routeToPage: function(url)
        {
            var newPageUrl = SITE_SUBFOLDER + String(url).replace(/.*\/neumeeditor\//g, "");
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

        url: SITE_URL + "images/",

        defaults: {
            image_file: "",
            glyph: 0,
            thumbnail: ""
        },

        initialize: function(options)
        {
            if (options !== undefined && options.url !== undefined)
            {
                this.url = String(options.url);
            }
        },

        /**
         * Get the absolute url to the image file.
         *
         * @returns {string}
         */
        getAbsoluteImageFile: function()
        {
            return STATIC_URL + this.get("image_file");
        },

        getAbsoluteThumbnail: function()
        {
            return STATIC_URL + this.get("thumbnail");
        }
    });

    var Name = Backbone.Model.extend({

        url: SITE_URL + "names/",

        defaults: {
            string: ""
        },

        initialize: function(options)
        {
            if (options !== undefined && options.url !== undefined)
            {
                this.url = String(options.url);
            }
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

    var Nomenclature = Backbone.Model.extend({
        urlRoot: SITE_URL + "nomenclature/",

        defaults: {
            nomenclature_name: ""
        },

        initialize: function(options)
        {
            if (options !== undefined && options.url !== undefined)
            {
                this.url = String(options.url);
            }
        }
    });

    /**
     * A relationship between a name and a nomenclature.
     */
    var NameNomenclatureMembership = Backbone.Model.extend({
        urlRoot: SITE_URL + "name-nomenclature-membership/",

        initialize: function(options)
        {
            this.url = String(options.url);
        },

        defaults: {
            id: undefined,
            name: undefined,
            nomenclature: undefined,
            glyph: undefined,
            name_string: undefined,
            nomenclature_string: undefined
        }
    });

    /**
     * A musical glyph, such as a punctum.
     */
    var Glyph = Backbone.Model.extend({

        urlRoot: SITE_URL + "glyphs/",

        //initialize: function(options)
        //{
        //    this.url = String(options.url);
        //},

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
            //id: 0,
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

    var NomenclatureCollection = Backbone.Collection.extend({
        model: Nomenclature,

        initialize: function(options)
        {
            this.url = String(options.url);
        },

        comparator: function(name)
        {
            // Newest names first
            return 0 - parseInt(name.get("id"));
        }
    });

    var NameNomenclatureMembershipCollection = Backbone.Collection.extend({
        model: NameNomenclatureMembership,

        initialize: function(options)
        {
            this.url = String(options.url);
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
        menuLinks.add(new Link().set({url:SITE_URL + "", text: "Neumes"}));
        menuLinks.add(new Link().set({url:SITE_URL + "nomenclatures/", text: "Nomenclatures"}));
        //menuLinks.add(new Link().set({url:SITE_URL + "styles/", text: "Styles"}));

        var menu = new MainMenuView({collection: menuLinks});
        App.navigation.show(menu);
    });

    App.module("Authentication", function(Authentication, App, Backbone, Marionette, $, _){
        this.startWithParent = false;
    });

    App.module("NomenclatureList", function(NomenclatureList, App, Backbone, Marionette, $, _){
        this.startWithParent = false;

        /*
         Item Views
         */

        var NomenclatureView = Backbone.Marionette.ItemView.extend({
            template: "#nomenclature-template",
            tagName: "tr",

            ui: {
                "deleteButton": 'button[name="delete"]'
            },

            events: {
                "click @ui.deleteButton": "destroyModel"
            },

            destroyModel: function()
            {
                this.model.destroy(
                    {
                        success: function(){
                            console.log("It worked.");
                        }
                    });
            }
        });

        var NomenclatureCompositeView = Backbone.Marionette.CompositeView.extend({
            childView: NomenclatureView,

            childViewContainer: "tbody",
            template: "#nomenclature-collection-template"
        });

        var CreateNomenclatureView = Backbone.Marionette.ItemView.extend({
            /**
             * The collection that the new glyph will be added to.
             */
            createdCollection: undefined,
            template: "#create-nomenclature-template",
            tagName: 'form class="form" action="#"',

            ui: {
                "nameField": "[name='nomenclature-name-field']",
                "statusDiv": ".status-message"
            },

            events: {
                "submit": "createButtonCallback"
            },

            initialize: function (options) {
                // Assign the collection which contains the created glyphs
                this.createdCollection = options.createdCollection;
            },

            createButtonCallback: function (event) {
                // Prevent the event from redirecting the page
                event.preventDefault();
                // Create the nomenclature
                var nomenclature = new Nomenclature(
                    {
                        url: SITE_URL + "nomenclatures/",
                        "nomenclature_name": this.ui.nameField.val()
                    });
                var that = this;
                nomenclature.save(
                    undefined,
                    {
                        success: function (event) {
                            // Manually copy the url.
                            nomenclature.url = nomenclature.get("url");
                            that.ui.statusDiv.html('<p class="alert alert-success" role="alert">Nomenclature "' + nomenclature.get("nomenclature_name") + '" saved successfully.</p>');
                            //that.ui.statusDiv.find("p").fadeOut(5000);
                            // Add the created glyph to the createdCollection
                            that.createdCollection.add(nomenclature);
                            // Empty the short code field
                            that.ui.nameField.val('');
                        },
                        error: function (model, event) {
                            that.ui.statusDiv.html('<p class="alert alert-danger" role="alert">Error saving nomenclature. - ' + event.responseText +  '<p>');
                            //that.ui.statusDiv.find("p").fadeOut(5000);
                        }
                    }
                );
                // Redirect to the edit page

            }
        });

        var NomenclatureDashboardView = Backbone.Marionette.LayoutView.extend({
            template: "#glyph-dashboard-template",

            regions: {
                glyphCreateRegion: ".glyph-create-region",
                glyphListRegion: ".glyph-list-region"
            },

            onShow: function() {
                var nomenclatureCollection = new NomenclatureCollection({url: "/neumeeditor/nomenclatures/"});
                nomenclatureCollection.fetch();
                this.glyphCreateRegion.show(new CreateNomenclatureView({createdCollection: nomenclatureCollection}));
                this.glyphListRegion.show(new NomenclatureCompositeView({collection: nomenclatureCollection}));
            }
        });

        /*
         ------------------------------------------------------
         Execution Code
         ------------------------------------------------------
         */

        this.start = function()
        {
            App.container.show(new NomenclatureDashboardView());
        };
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
                    "thumbnail": this.model.getAbsoluteThumbnail()
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
                event.preventDefault();
                AppRouter.routeToPage(this.model.get("url"));
            },

            onShow: function() {
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

        var CreateGlyphView = Backbone.Marionette.ItemView.extend({
            /**
             * The collection that the new glyph will be added to.
             */
            createdCollection: undefined,
            template: "#create-glyph-template",
            tagName: 'form class="form" action="#"',

            ui: {
                "shortCodeField": "[name='glyph-short-code-field']",
                "statusDiv": ".status-message"
            },

            events: {
                "submit": "createGlyphButtonCallback"
            },

            initialize: function(createdCollection) {
                // The model is always a blank glyph
                this.generateNewEmptyGlyph();
                // Assign the collection which contains the created glyphs
                this.createdCollection = createdCollection;
            },

            generateNewEmptyGlyph: function() {
                this.model = new Glyph();
            },

            createGlyphButtonCallback: function(event)
            {
                // Prevent the event from redirecting the page
                event.preventDefault();
                // Flip the reference
                var newGlyph = this.model;
                var that = this;
                this.model.save(
                    {"short_code": this.ui.shortCodeField.val()},
                    {
                        success: function(event) {
                            that.ui.statusDiv.html('<p class="alert alert-success" role="alert">Glyph "<a href="' + newGlyph.get("url") + '">' + newGlyph.get("short_code") + '</a>" saved successfully.</p>');
                            //that.ui.statusDiv.find("p").fadeOut(5000);
                            // Add the created glyph to the createdCollection
                            that.createdCollection.add(newGlyph);
                            // Generate a new empty glyph
                            that.generateNewEmptyGlyph();
                            // Empty the short code field
                            that.ui.shortCodeField.val('');
                        },
                        error: function(model, event) {
                            that.ui.statusDiv.html('<p class="alert alert-danger" role="alert">Error saving glyph. - ' + event.responseText +  '<p>');
                            //that.ui.statusDiv.find("p").fadeOut(5000);
                        }
                    }
                );
                // Redirect to the edit page

            }
        });

        var GlyphDashboardView = Backbone.Marionette.LayoutView.extend({
            template: "#glyph-dashboard-template",

            regions: {
                glyphCreateRegion: ".glyph-create-region",
                glyphListRegion: ".glyph-list-region"
            },

            onShow: function() {
                var glyphCollection = new GlyphCollection({url: "/neumeeditor/glyphs/"});
                glyphCollection.fetch();
                this.glyphCreateRegion.show(new CreateGlyphView(glyphCollection));
                this.glyphListRegion.show(new GlyphCompositeView({collection: glyphCollection}));
            }
        });

        /*  
        ------------------------------------------------------
        Execution Code
        ------------------------------------------------------
        */

        this.start = function()
        {
            App.container.show(new GlyphDashboardView());
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

        /**
         * Edit the properties of the glyph.
         */
        var EditGlyphPropertiesView = Backbone.Marionette.ItemView.extend({
            template: "#edit-glyph-properties-template",

            events: {
                "submit": "saveProperties"
            },

            ui: {
                commentsBox: ".comments-box",
                statusDiv: ".property-status-message"
            },

            saveProperties: function(event)
            {
                console.log("Saving properties");
                // Prevent default functionality
                event.preventDefault();
                var that = this;
                this.model.save(
                    {
                        comments: String(this.ui.commentsBox.val())
                    },
                    {
                        success: function() {
                            console.log("Success");
                            that.ui.statusDiv.html('<p class="alert alert-success" role="alert">Properties updated successfully.</p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        },
                        error: function(model, event) {
                            console.log("Failure.");
                            that.ui.statusDiv.html('<p class="alert alert-danger">Error saving. - ' + event.responseText +  '<p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        }
                    }
                );
            }
        });

        /**
         * A view that allows the user to create a NameNomenclatureRelationship.
         */
        var CreateNameNomenclatureMembershipView = Backbone.Marionette.ItemView.extend({
            tagName: "div",

            template: "#create-name-nomenclature-membership-template",

            /**
             * Collection of names
             */
            names: undefined,
            /**
             * Collection of nomenclatures
             */
            nomenclatures: undefined,
            /**
             * Collection of nameNomenclatureMemberships for when it's done.
             */
            nameNomenclatureMemberships: undefined,

            ui: {
                'nameField': "select[name='name']",
                'nomenclatureField': "select[name='nomenclature']",
                'statusDiv': ".status-message"
            },

            events: {
                'submit': 'onSubmit'
            },

            initialize: function(options)
            {
                this.names = options.names;
                this.nomenclatures = options.nomenclatures;
                this.nameNomenclatureMemberships = options.nameNomenclatureMemberships;

                // Re-render if name and nomenclature list changes
                this.listenTo(this.names, 'all', this.test);
                this.listenTo(this.nomenclatures, 'all', this.test);
            },

            test: function() {
                console.log("IT HAPPENED.");
                this.render();
            },

            /**
             * Serialize a list of names and nomenclatures.
             *
             * @returns {{names: string[], nomenclatures: string[]}}
             */
            serializeData: function()
            {
                return {
                    names: this.names.toJSON(),
                    nomenclatures: this.nomenclatures.toJSON()
                };
            },


            onSubmit: function(event)
            {
                event.preventDefault();
                console.log("submit");
                // Create the membership object
                var membership = new NameNomenclatureMembership(
                    {
                        url: SITE_URL + "name-nomenclature-memberships/",
                        name: this.ui.nameField.val(),
                        nomenclature: this.ui.nomenclatureField.val()
                    }
                );
                console.log("membership:", membership.toJSON());
                // Save it to the server
                var that = this;
                membership.save(null,
                    {
                        success: function()
                        {
                            // Manually copy the url
                            membership.url = membership.get("url");
                            // Add the membership to the created ones
                            that.nameNomenclatureMemberships.add(membership);
                            // Reset the option fields to default
                            that.ui.nameField.val("null");
                            that.ui.nomenclatureField.val("null");
                            // Display the user status message
                            that.ui.statusDiv.html('<p class="alert alert-success" role="alert">Name - Nomenclature membership saved successfully.</p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        },
                        error: function(model, event)
                        {
                            console.log("event:", model, event);
                            that.ui.statusDiv.html('<p class="alert alert-warning" role="alert">Error: Name -' + event.responseText + '</p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        }
                    }
                );
            }
        });

        var EditSingleNameNomenclatureMembershipView = Backbone.Marionette.ItemView.extend({
            tagName: "tr",
            template: "#edit-single-name-nomenclature-membership-template",

            ui: {
                'deleteButton': 'button[name="delete"]'
            },

            events: {
                "click @ui.deleteButton": "destroyModel"
            },

            destroyModel: function()
            {
                this.model.destroy();
            }
        });

        var EditSingleImageView = Backbone.Marionette.ItemView.extend({
            tagName: "div",

            template: "#edit-single-image-template",

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
                    "thumbnail": this.model.getAbsoluteThumbnail()
                };
            },

            destroyModel: function()
            {
                event.preventDefault();
                this.model.destroy();
            }
        });

        /**
         * View for editing a single name object.
         */
        var EditSingleNameView = Backbone.Marionette.ItemView.extend({

            tagName: "form",

            template: "#edit-single-name-template",

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
                            that.ui.statusDiv.html('<p class="alert alert-success" role="alert">Name saved successfully.</p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                            return that.trigger("submit");
                        },
                        error: function(model, event) {
                            that.ui.statusDiv.html('<p class="alert alert-danger" role="alert">Error saving name. - ' + event.responseText +  '<p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        }
                    }
                );
            },

            destroyModel: function()
            {
                event.preventDefault();
                this.model.destroy();
                return this.trigger("destroy");
            }
        });

        var CreateImagesView = Backbone.Marionette.ItemView.extend({
            createdCollection: undefined,
            template: "#upload-image-template",
            dropzoneObject: undefined,

            ui: {
                "dropzone": ".dropzone-form"
            },

            initialize: function(options)
            {
                if(options !== undefined)
                {
                    if (options.createdCollection !== undefined)
                    {
                        this.createdCollection = options.createdCollection;
                    }
                    if (options.glyphId !== undefined)
                    {
                        this.setGlyphId(options.glyphId);
                    }
                }
            },

            /**
             * Set the view glyph ID.
             *
             * @param idNum Glyph ID int,
             */
            setGlyphId: function(idNum)
            {
                this.glyphId = getAbsoluteGlyphUrl(parseInt(idNum));
            },

            onShow: function()
            {
                // Build the dropzone
                this.dropzoneObject = new Dropzone(this.ui.dropzone.selector,
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
                // Set up the callbacks
                var that = this;
                this.dropzoneObject.on("success",
                    function(file, attributes) {
                        var newModel = new Image({url: attributes.url});
                        newModel.set(attributes);
                        newModel.set("glyph", that.glyphId);
                        that.createdCollection.add(newModel);
                    }
                );
            }
        });

        var CreateNameView = Backbone.Marionette.ItemView.extend({
            glyphUrl: undefined,
            nameCollection: undefined,
            template: '#create-single-name-template',

            events: {
                "submit": "onSubmit"
            },

            ui: {
                nameStringField: "input[name='string']",
                statusDiv: ".status-message"
            },

            initialize: function(options)
            {
                // We will use the glyphId to construct the name
                this.glyphUrl = options.glyphUrl;
                // The collection of names we will add to
                this.nameCollection = options.nameCollection;
            },

            onSubmit: function(event)
            {
                // Prevent default functionality
                event.preventDefault();

                // Flip the self reference.
                var that = this;

                // Grab values from the form fields
                var name = new Name({
                    glyph: this.glyphUrl,
                    string: String(this.ui.nameStringField.val())
                });

                name.save(null,
                    {
                        success: function() {
                            console.log("name test:", name);
                            // For some reason URL isn't getting copied unless we do it manually
                            name.url = name.get("url");
                            // Add the new name to the collection
                            that.nameCollection.add(name);
                            // Print the success message
                            that.ui.statusDiv.html('<p class="alert alert-success" role="alert">Name saved successfully.</p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                            // Clear the user input
                            that.ui.nameStringField.val("");
                        },
                        error: function(model, event) {
                            that.ui.statusDiv.html('<p class="alert alert-danger" role="alert">Error saving name. - ' + event.responseText +  '<p>');
                            that.ui.statusDiv.find("p").fadeOut(2500);
                        }
                    }
                );
            }
        });

        /*
        Composite Views
        */

        var EditNameNomenclatureMembershipsView = Backbone.Marionette.CompositeView.extend({
            childView: EditSingleNameNomenclatureMembershipView,

            childViewContainer: ".name-list",
            template: "#edit-name-nomenclature-membership-collection-template"
        });

        var EditNamesView = Backbone.Marionette.CollectionView.extend({
            childView: EditSingleNameView,

            childViewContainer: ".name-list",

            childViewOptions: {},

            initialize: function(options)
            {
                this.childViewOptions.nomenclatures = options.nomenclatures;
            }
        });

        var EditImagesView = Backbone.Marionette.CompositeView.extend({
            childView: EditSingleImageView,

            childViewContainer: ".images",
            template: "#edit-image-collection-template"
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
                nameNomenclatureMembershipCreateArea: ".name-nomenclature-membership-create-area",
                nameNomenclatureMembershipViewArea: ".name-nomenclature-membership-view-area",
                imageUploadArea: ".image-upload-area",
                imagesEditArea: ".images-area",
                glyphPropertiesArea: ".glyph-properties-area"
            },

            initialize: function(options)
            {
                this.glyphNames = new NameCollection();
                this.glyphImages = new ImageCollection();
                this.nomenclatures = options.nomenclatures;

                // Create the subViews
                this.editNamesView = new EditNamesView(
                    {
                        collection: this.glyphNames,
                        nomenclatures: this.nomenclatures
                    }
                );
                this.createNamesView = new CreateNameView({
                    glyphUrl: this.model.get("url"),
                    nameCollection: this.glyphNames
                });
                this.editImagesView = new EditImagesView({
                    collection: this.glyphImages
                });
                this.createImagesView = new CreateImagesView({
                    glyphId: this.model.get("id"),
                    createdCollection: this.glyphImages
                });

                // Load the names and images
                this.loadNamesAndImages();
            },



            /**
             * Extract the names and images from the model.
             */
            loadNamesAndImages: function()
            {
                // Set the glyph ids on the child views
                this.createImagesView.setGlyphId(this.model.get("id"));
                // Load the models into the collections
                this.glyphNames.reset(this.model.get("name_set"));
                this.glyphImages.reset(this.model.get("image_set"));
            },

            onShow: function()
            {
                // Show the subviews
                this.namesArea.show(this.editNamesView,{ preventDestroy: true });
                this.nameCreateArea.show(this.createNamesView,{ preventDestroy: true });
                this.imagesEditArea.show(this.editImagesView,{ preventDestroy: true });
                this.imageUploadArea.show(this.createImagesView,{ preventDestroy: true });

                this.glyphPropertiesArea.show(new EditGlyphPropertiesView({model: this.model}));

                // NameNomenclatureMembershipCollection
                var memberships = new NameNomenclatureMembershipCollection({url: SITE_URL + "name-nomenclature-memberships/glyph/" + this.model.get("id")});
                memberships.fetch();

                this.nameNomenclatureMembershipCreateArea.show(new CreateNameNomenclatureMembershipView(
                    {
                        names: this.glyphNames,
                        nomenclatures: this.nomenclatures,
                        nameNomenclatureMemberships: memberships
                    }));
                this.nameNomenclatureMembershipViewArea.show(new EditNameNomenclatureMembershipsView({collection: memberships}));
            },

            onRender: function()
            {
                this.editNamesView.render();
                this.createNamesView.render();
                this.editImagesView.render();
                this.createImagesView.render();
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

        //var editor;
        //
        //this.start = function() {
        //    editor = new AppLayoutView({model: glyph});
        //};
        
        this.initializeId = function(id)
        {
            glyphId = parseInt(id);
            glyph.url = "/neumeeditor/glyph/" + glyphId + "/";

            // Get the nomenclature list that we will use
            var nomenclatures = new NomenclatureCollection({url: "/neumeeditor/nomenclatures"});
            nomenclatures.fetch({success: function() {console.log("Got nomenclatures", nomenclatures);}});

            glyph.fetch({success: function() {
                // Build the main view
                var editor = new AppLayoutView(
                    {
                        model: glyph,
                        nomenclatures: nomenclatures
                    }
                );
                // Render the LayoutView
                // Glyph data loaded, so load the names, etc.
                editor.loadNamesAndImages();
                App.container.show(editor);
            }});
        };


    });
    App.start();

})(jQuery);
