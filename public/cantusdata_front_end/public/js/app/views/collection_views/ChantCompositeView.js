define( ['App', 'backbone', 'marionette', 'jquery',
        "views/item_views/ChantItemView",
        "singletons/GlobalEventHandler",
        "models/StateSwitch"],
    function(App, Backbone, Marionette, $,
             ChantItemView,
             GlobalEventHandler,
             StateSwitch) {

"use strict";

/**
 * A composite view.
 */
return Marionette.CompositeView.extend
({
    childView: ChantItemView,
    childViewContainer: ".accordion",
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

    ui: {
        errorMessages: ".error-messages"
    },

    initialize: function()
    {
        this.collection = new Backbone.Collection();
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
        // "collapse-1" becomes 1, etc.
        var chant = parseInt(event.target.id.split('-')[1], 10);
        this.chantStateSwitch.setValue(chant - 1, true);
        GlobalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue() + 1);
    },

    foldChantCallback: function(event)
    {
        var chant = parseInt(event.target.id.split('-')[1], 10);
        this.chantStateSwitch.setValue(chant - 1, false);
        var newGlobalValue = this.chantStateSwitch.getValue();
        if (newGlobalValue !== undefined)
        {
            // Increase it by one because the GUI isn't 0-indexed, but the StateSwitch is.
            newGlobalValue += 1;
        }
        GlobalEventHandler.trigger("ChangeChant", newGlobalValue);
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
        // We need to display messages if there are no chants.
        if (this.collection.length === 0)
        {
            // No chants
            this.ui.errorMessages.html("This folio does not contain musical data.");
        }
        else
        {
            // Some chants
            this.ui.errorMessages.html();
        }
    },

    /**
     * Set the URL of the collection and fetch the data.
     *
     * @param url
     */
    setUrl: function(url)
    {
        this.collection.url = url;
        this.collection.fetch({success: this.render});
    },

    /**
     * Reset the collection.
     */
    resetCollection: function()
    {
        this.collection.reset();
        this.render();
    }
});
});