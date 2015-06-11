define( ['App', 'backbone', 'marionette', 'jquery',
        "views/item_views/ChantItemView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             ChantItemView,
             GlobalEventHandler) {

"use strict";

/**
 * A composite view.
 */
return Marionette.CompositeView.extend({
    childView: ChantItemView,
    childViewContainer: ".accordion",
    template: "#chant-composite-template",

    /**
     * The chant that bootstrap has unfolded
     */
    unfoldedChant: null,

    ui: {
        errorMessages: ".error-messages"
    },

    collectionEvents: {
        'sync reset': 'collectionLoad'
    },

    childEvents: {
        'fold:chant': 'chantFolded',
        'unfold:chant': 'chantUnfolded'
    },

    initialize: function()
    {
        // Set the initial open chant state
        this.unfoldedChant = this.getOption('unfoldedChant');

        // Convert undefined to null and numerical strings to numbers
        /* jshint eqnull:true */
        if (this.unfoldedChant == null)
            this.unfoldedChant = null;
        else
            this.unfoldedChant |= 0;

        // Unfold a chant when the global ChangeChant event is triggered
        this.listenTo(GlobalEventHandler, "ChangeChant", this.setUnfoldedChant);
    },

    /**
     * Pass child views their initial state when they are created
     *
     * @param model
     * @param index
     * @returns {{open: boolean}}
     */
    childViewOptions: function (model, index)
    {
        /* jshint eqnull:true */

        return {
            open: this.unfoldedChant != null && this.unfoldedChant - 1 === index
        };
    },

    /**
     * Callback triggered when a child view's panel is collapsed
     * by the user
     *
     * @param child the child view
     */
    chantFolded: function (child)
    {
        // Get the 1-indexed position of the child
        var chant = this.collection.indexOf(child.model) + 1;

        if (this.unfoldedChant === chant)
        {
            this.unfoldedChant = null;
            GlobalEventHandler.trigger("ChangeChant", null);
        }
    },

    /**
     * Callback triggered when a child view's panel is unfolded
     * by the user
     *
     * @param child the child view
     */
    chantUnfolded: function (child)
    {
        // Get the 1-indexed position of the child
        var chant = this.collection.indexOf(child.model) + 1;

        if (this.unfoldedChant !== chant)
        {
            this.unfoldedChant = chant;
            GlobalEventHandler.trigger("ChangeChant", chant);
        }
    },

    /**
     * Update the UI when the global open chant is changed
     *
     * @param index 0 to infinity
     */
    setUnfoldedChant: function(index)
    {
        var child;

        /* Check for a chant value of null or undefined */
        /* jshint eqnull:true */
        if (index == null)
        {
            // If the chant is closed then collapse the chant panel
            if (this.unfoldedChant !== null)
            {
                var chant = this.unfoldedChant;
                this.unfoldedChant = null;

                child = this.children.findByIndex(chant - 1);
                if (child)
                    child.ui.collapse.collapse('hide');
            }
        }
        else
        {
            // Coerce to integer
            index |= 0;

            // If the chant has changed then expand the correct panel
            // (this will automatically collapse other panels as necessary)
            if (this.unfoldedChant !== index)
            {
                this.unfoldedChant = index;

                child = this.children.findByIndex(this.unfoldedChant - 1);
                if (child)
                    child.ui.collapse.collapse('show');
            }
        }
    },

    onRender: function ()
    {
        this.collectionLoad();
    },

    /**
     * Update the error messages when the collection is loaded or reset
     *
     * TODO(wabain): refactor the error messages to be an emptyView
     */
    collectionLoad: function()
    {
        // Catch the case where the collection is loaded before the view is rendered
        if (typeof this.ui.errorMessages === 'string')
            return;

        // We need to display messages if there are no chants.
        if (this.collection.length === 0)
        {
            // No chants
            this.ui.errorMessages.html("This folio does not contain musical data.");
        }
        else
        {
            // Some chants
            this.ui.errorMessages.empty();
        }
    }
});
});