import Marionette from 'marionette';

/**
 * Have the root element of this view occupy the remaining
 * height of the viewport. This is achieved pretty hackily
 * by setting the `propagate-height` class on the ancestors.
 */
var FillViewportHeightBehavior = Marionette.Behavior.extend({
    onAttach() {
        this.$el.addClass('propagate-height');
        this.$el.parentsUntil('html').addClass('propagate-height');
    },

    onBeforeDestroy() {
        this.$el.removeClass('propagate-height');
        this.$el.parentsUntil('html').removeClass('propagate-height');
    }
});

export default FillViewportHeightBehavior;
