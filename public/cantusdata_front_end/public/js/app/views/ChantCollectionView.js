define( ['App', 'backbone', 'marionette', 'jquery',
        "collections/ChantCollection",
        "models/StateSwitch",
        "views/CantusAbstractView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             ChantCollection,
             StateSwitch,
             CantusAbstractView,
             GlobalEventHandler,
             template) {

"use strict";

/**
 * Depricated in favour of ChantCompositeView.
 */
return CantusAbstractView.extend
({
    /**
     * Useful switch if you want different functionality on initial load.
     */
    alreadyLoaded: false,

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
        _.bindAll(this, 'render', 'setUnfoldedChant', 'unfoldChantCallback',
            'foldChantCallback', 'afterFetch');
        this.template = _.template($('#chant-collection-template').html());
        this.emptyTemplate = _.template($('#empty-chant-collection-template').html());

        this.collection = new ChantCollection();

        // TODO: Figure out why this is still rendering multiple times
        this.listenTo(this.collection, 'sync', this.render);
        // Set the unfolded chant when the global state changes!
        this.listenTo(GlobalEventHandler, "ChangeChant", this.setUnfoldedChant);

        this.alreadyLoaded = 0;
    },

    /**
     * Callback for when a chant is "unfolded" by Bootstrap.
     *
     * @param event
     */
    unfoldChantCallback: function(event)
    {
        // "collapse-1" becomes 1, etc.
        var chant = parseInt(event.target.id.split('-')[1], 10) + 1;
        this.chantStateSwitch.setValue(chant, true);
        GlobalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue());
        GlobalEventHandler.trigger("SilentUrlUpdate");
    },

    foldChantCallback: function(event)
    {
        var chant = parseInt(event.target.id.split('-')[1], 10) + 1;
        this.chantStateSwitch.setValue(chant, false);
        GlobalEventHandler.trigger("ChangeChant", this.chantStateSwitch.getValue());
        GlobalEventHandler.trigger("SilentUrlUpdate");
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

    afterFetch: function()
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
        this.collection.url = url;
        this.collection.fetch({success: this.afterFetch});
        // Reset the chant if this isn't the initial load
        if (this.alreadyLoaded === true)
        {
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
    },

    /**
     * Render the collection.
     *
     * @returns {*}
     */
    render: function()
    {
        // TODO: Figure out why this gets called 4 times
        if (this.collection.length === 0)
        {
            $(this.el).html(this.emptyTemplate());
        }
        else
        {
            // Render out the template
            $(this.el).html(this.template(
                {
                    chants: this.collection.toJSON(),
                    unfoldedChant: this.unfoldedChant
                }
            ));
        }
        GlobalEventHandler.trigger("renderView");
        return this.trigger('render', this);
    },

    resetCollection: function()
    {
        this.collection.reset();
    }
});
});
