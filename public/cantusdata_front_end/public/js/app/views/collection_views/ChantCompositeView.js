define( ['App', 'backbone', 'marionette', 'jquery',
        "views/item_views/ChantItemView",
        "singletons/GlobalEventHandler",
        "models/StateSwitch",
        "config/GlobalVars"],
    function(App, Backbone, Marionette, $,
             ChantItemView,
             GlobalEventHandler,
             StateSwitch,
             GlobalVars) {

"use strict";

/**
 * A composite view.
 */
return Marionette.CompositeView.extend
({
    childView: ChantItemView,
    childViewContainer: "#accordion",
    template: "#chant-composite-template",

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
        // Unfold a chant when changechant event happens
        this.listenTo(GlobalEventHandler, "ChangeChant", this.setUnfoldedChant);
    },

    /**
     * Callback for when a chant is "unfolded" by Bootstrap.
     *
     * @param event
     */
    unfoldChantCallback: function(event)
    {
        //console.log("unfoldChantCallback() begin.");
        // "collapse-1" becomes 1, etc.
        var chant = parseInt(event.target.id.split('-')[1], 10) + 1;
        this.chantStateSwitch.setValue(chant, true);

        //console.log(chant);

        GlobalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue());
        GlobalEventHandler.trigger("SilentUrlUpdate");
        //console.log("unfoldChantCallback() end.");
    },

    foldChantCallback: function(event)
    {
        //console.log("foldChantCallback() begin.");
        var chant = parseInt(event.target.id.split('-')[1], 10) + 1;
        this.chantStateSwitch.setValue(chant, false);

        //console.log(chant);

        GlobalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue());
        GlobalEventHandler.trigger("SilentUrlUpdate");
        //console.log("foldChantCallback() end.");
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
            this.unfoldedChant = parseInt(index, 10) - 1;
        }
    },

    onRender: function()
    {
        // Make a new StateSwitch object that we will use to keep track
        // of the open chant.
        this.chantStateSwitch = new StateSwitch(this.collection.length);
    },

    /**
     * Set the URL of the collection and fetch the data.
     *
     * @param url
     */
    setUrl: function(url)
    {
        console.log("setUrl() begin.");
        this.collection.url = url;
        this.collection.fetch({success: this.render});
        // Reset the chant if this isn't the initial load
        if (this.alreadyLoaded === true) {
            this.unfoldedChant = undefined;
            GlobalEventHandler.trigger("ChangeChant", undefined);
            // If we don't update the URL then the chant persists when we
            // change the folio...
            GlobalEventHandler.trigger("SilentUrlUpdate");
        }
        else
        {
            this.alreadyLoaded = true;
        }
        console.log("setUrl() end.");
    },

    /**
     * Reset the collection.
     */
    resetCollection: function()
    {
        this.collection.reset();
    },

    /**
     * Set the collection.
     *
     * @param collection
     */
    setCollection: function(collection)
    {
        this.collection = collection;
    }
});
});