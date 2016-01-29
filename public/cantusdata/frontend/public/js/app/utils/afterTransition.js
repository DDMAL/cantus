define([
    "underscore",
    "jquery"
], function (_, $)
{
    'use strict';

    /**
     * Call the callback function after the transitions for the element have completed,
     * or after the given number of milliseconds have elapsed if it is not possible
     * to detect the transition end.
     *
     * @param {jQuery} jqElem
     * @param {number} fallbackMs
     * @param {function} callback
     * @param {Object} context
     */
    return function afterTransition(jqElem, fallbackMs, callback, ctx)
    {
        // These jQuery properties are defined by Bootstrap
        jqElem
            .one($.support.transition.end, _.bind(callback, ctx))
            .emulateTransitionEnd(fallbackMs);
    };
});
