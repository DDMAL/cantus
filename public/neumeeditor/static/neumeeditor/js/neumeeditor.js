(function($){
    "use strict";

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

    var App = new Backbone.Marionette.Application();

    App.on('initialize:before', function(options)
    {
        options.anotherThing = true; // Add more data to your options
    });
    App.on('initialize:after', function(options)
    {
        console.log('Initialization Finished');
    });
    App.on('start', function(options)
    {
        Backbone.history.start(); // Great time to do this
    });

    // Create a region. It will control what's in the #container element.
    App.container = new Backbone.Marionette.Region
    ({
        el: "#container"
    });

    // Add a view to the region. It will automatically render immediately.
    //    region.show(new MyView());

    // Close out the view that's currently there and render a different view.
    //    region.show(new MyOtherView());

    // Close out the view and display nothing in #container.
    //    region.close();

    App.module("authentication", function(myModule, App, Backbone, Marionette, $, _){
        this.startWithParent = false;
    });

    App.module("glyphEdit", function(myModule, App, Backbone, Marionette, $, _){
        this.startWithParent = true;

        var SingleLink = Backbone.Marionette.ItemView.extend({
           tagName: "li",
           template: _.template("<a href='<%-path%>'><%-path%></a>")
        });

        var Name = Backbone.Model.extend({
            initialize: function(options)
            {
                this.url = String(options.url);
            },

            defaults: {string: "", short_code: ""}
        });

        var NameCollection = Backbone.Collection.extend({
            model: Name
        });

        var Glyph = Backbone.Model.extend({

            initialize: function(options)
            {
                this.url = String(options.url);
            },

            /**
             * Get a collection containing the Glyph's names.
             *
             * @returns {NameCollection}
             */
            getNameCollection: function()
            {
                var output = new NameCollection();
                var nameArray = this.get("name_set");
                console.log(nameArray);
                for (var i = 0; i < nameArray.length; i++)
                {
                    console.log(String(nameArray[i]));
                    var nameModel = new Name({url: String(nameArray[i])});
                    output.add(nameModel);
                    nameModel.fetch();
                }
                console.log(output.toJSON());
                return output;
            }
        });

        /**
         * View for editing a single name object.
         */
        var EditSingleNameView = Backbone.Marionette.ItemView.extend({
            tagName: "form",
            template: _.template($('#edit-single-name-template').html()),
            modelEvents: { "change": "render" },
            events: { "submit": "submit" },
            submit: function(event) {
                // Prevent default functionality
                event.preventDefault();
                // Grab values from the form fields
                this.model.set({
                    string: String(this.$("input[name='string']").val()),
                    short_code: String(this.$("input[name='short_code']").val())
                });
                this.model.save();
            }
        });

        var EditNamesView = Backbone.Marionette.CollectionView.extend({
            tagName: 'ul',
            childView: EditSingleNameView
        });

        /**
         * View for looking at a single glyph object.
         */
        var SingleGlyph = Backbone.Marionette.ItemView.extend({
            tagName: "li",
            template: _.template("")
        });

        var EditSingleGlyphView = Backbone.Marionette.ItemView.extend({

        });

        var ListView = Backbone.Marionette.CollectionView.extend({
            tagName: 'ul',
            childView: SingleLink
        });

        var glyph = new Glyph({url: "http://localhost:8000/neumeeditor/glyph/1/"});


        this.start = function()
        {
            console.log("Starting...");
            glyph.fetch({success: function(){
                var glyphNames = glyph.getNameCollection();
                console.log(glyphNames);
                (new EditNamesView({
                    collection: glyphNames,
                    el: '.link-area'
                })).render();
            }});
        };


    });
    console.log("start app");
    App.start();

})(jQuery);
