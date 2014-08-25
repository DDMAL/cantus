(function($){
    "use strict";

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

        var Name = Backbone.Model.extend({});

        var Glyph = Backbone.Model.extend({

            getNameCollection: function() {

            }
        });

        /**
         * View for editing a single name object.
         */
        var EditSingleNameView = Backbone.Marionette.ItemView.extend({
            tagName: "form",
            template: _.template($('#edit-single-name-template').html())
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

        var ListView = Backbone.Marionette.CollectionView.extend({
            tagName: 'ul',
            childView: SingleLink
        });

        var list = new Backbone.Collection([
            {path: 'http://google.com'},
            {path: 'http://mojotech.com'},
        ]);

        this.start = function()
        {
            console.log("Starting...");
            (new EditNamesView({
                collection: list,
                el: '.link-area'
            })).render();
        };


    });
    console.log("start app");
    App.start();

})(jQuery);
