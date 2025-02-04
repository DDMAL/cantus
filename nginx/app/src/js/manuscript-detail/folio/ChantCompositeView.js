import Radio from 'backbone.radio';
import Marionette from 'marionette';
import ChantItemView from "./ChantItemView";

var manuscriptChannel = Radio.channel('manuscript');

import template from './chant-composite.template.html';

export default Marionette.CollectionView.extend({
    childView: ChantItemView,
    childViewContainer: ".accordion",

    template,

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

    initialize: function () {
        // Set the initial open chant state
        var unfoldedChant = manuscriptChannel.request('chant');

        // Convert undefined to null and numerical strings to numbers
        if (unfoldedChant == null) // eslint-disable-line eqeqeq
            unfoldedChant = null;
        else
            unfoldedChant |= 0; // eslint-disable-line no-bitwise

        this.unfoldedChant = unfoldedChant;

        // Unfold a chant when the global chant is changed
        this.listenTo(manuscriptChannel, 'change:chant', this.setUnfoldedChant);
    },

    /**
     * Pass child views their initial state when they are created
     *
     * @param model
     * @param index
     * @returns {{open: boolean}}
     */
    childViewOptions: function (model, index) {
        return {
            open: this.unfoldedChant != null && this.unfoldedChant - 1 === index // eslint-disable-line eqeqeq
        };
    },

    /**
     * Callback triggered when a child view's panel is collapsed
     * by the user
     *
     * @param child the child view
     */
    chantFolded: function (child) {
        // Get the 1-indexed position of the child
        var chant = this.collection.indexOf(child.model) + 1;

        if (this.unfoldedChant === chant) {
            this.unfoldedChant = null;
            manuscriptChannel.request('set:chant', null);
        }
    },

    /**
     * Callback triggered when a child view's panel is unfolded
     * by the user
     *
     * @param child the child view
     */
    chantUnfolded: function (child) {
        // Get the 1-indexed position of the child
        var chant = this.collection.indexOf(child.model) + 1;

        if (this.unfoldedChant !== chant) {
            this.unfoldedChant = chant;
            manuscriptChannel.request('set:chant', chant);
        }
    },

    /**
     * Update the UI when the global open chant is changed
     *
     * @param index 0 to infinity
     */
    setUnfoldedChant: function (index) {
        var child;

        /* Check for a chant value of null or undefined */
        if (index == null) // eslint-disable-line eqeqeq
        {
            // If the chant is closed then collapse the chant panel
            if (this.unfoldedChant !== null) {
                var chant = this.unfoldedChant;
                this.unfoldedChant = null;

                child = this.children.findByIndex(chant - 1);
                if (child)
                    child.collapseContent();
            }
        }
        else {
            // Coerce to integer
            index |= 0; // eslint-disable-line no-bitwise

            // If the chant has changed then expand the correct panel
            // (this will automatically collapse other panels as necessary)
            if (this.unfoldedChant !== index) {
                this.unfoldedChant = index;

                child = this.children.findByIndex(this.unfoldedChant - 1);
                if (child)
                    child.expandContent();
            }
        }
    },

    onRender: function () {
        this.collectionLoad();
    },

    /**
     * Update the error messages when the collection is loaded or reset
     *
     * TODO(wabain): refactor the error messages to be an emptyView
     */
    collectionLoad: function () {
        // Catch the case where the collection is loaded before the view is rendered
        if (typeof this.ui.errorMessages === 'string')
            return;

        // We need to display messages if there are no chants.
        if (this.collection.length === 0) {
            // No chants
            this.ui.errorMessages.html("No chant records begin on this page or folio side.");
        }
        else {
            // Some chants
            this.ui.errorMessages.empty();
        }
    }
});
