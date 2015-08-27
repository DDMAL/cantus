define(function ()
{
    "use strict";

    /**
     * Return true if the last child view of a Marionette collection view
     * is within the visible portion of a containing element.
     *
     * @param collectionView
     * @param container
     * @returns {boolean}
     */
    function lastChildVisible(collectionView, container)
    {
        var lastChild = collectionView.children.last();

        if (!lastChild)
            return false;

        // Sometimes this can be triggered while the last item is not in the layout.
        // In that case, we just ignore the call.
        var elemTop = lastChild.$el.offset().top - container.offset().top;
        var visibleBottom = container.height();

        // If the top of the element is above the bottom of the container and below
        // the top of the screen, return true.
        return elemTop >= 0 && elemTop <= visibleBottom;
    }

    return lastChildVisible;
});
