define(["jquery", "underscore", "marionette"], function ($, _, Marionette)
{
    "use strict";

    /**
     * Aggregates and dispatches callbacks to manage the sizing of views which require
     * JavaScript maintenance. The behavior automatically handles resizing when the view is shown
     * and when the window is resized. It can be triggered by the view using the recalculate:size
     * event.
     *
     * Options:
     *
     *  - `target` {?string} Selector for an element to expand so that its height fills the screen.
     *
     *    Defaults to the view's root element. Set the value to `false` to disable it.
     *
     *  - `action` {?string|Function} Callback method to invoke on each resize calculation.
     *
     *    Called with the `resize` event object if the callback is triggered as the result
     *    of the window resizing.
     *
     *  - `priority {Number} Controls the ordering of callbacks. Views with a higher priority
     *    get resized first. Default: 1000
     *
     * @constructor
     */
    var ResizeBehavior = Marionette.Behavior.extend({
        defaults: function ()
        {
            return {
                action: null,
                target: null,
                priority: 1000
            };
        },

        initialize: function ()
        {
            this.priority = this.options.priority;
            this.listenerAttached = false;
        },

        // Lifecycle events

        /** Attach a listener when the view is rendered */
        onRender: function ()
        {
            ResizeBehavior.addListener(this);
        },

        /** Size the view when it is shown */
        onShow: function ()
        {
            this.doResize();
        },

        /** Remove the listener when it is destroyed */
        onDestroy: function ()
        {
            ResizeBehavior.removeListener(this);
        },

        /** Expose a method which can be called using triggerMethod */
        onRecalculateSize: function ()
        {
            this.doResize();
        },

        /** Do the resizing for the view */
        doResize: function (event)
        {
            this.resizeTarget();
            this.doResizeAction(event);
        },

        /** Resize the target so that it stretches to the bottom of the screen */
        resizeTarget: function ()
        {
            var targetSelector = this.options.target;

            if (targetSelector === false)
                return;

            var target = targetSelector ? this.$(targetSelector) : this.view.$el;

            // Stretch the target to the bottom of the screen
            if (target && target.length > 0)
                target.css('height', ResizeBehavior.$window.height() - target.offset().top);
        },

        /** Execute the resize action */
        doResizeAction: function (event)
        {
            var action = this.options.action;

            if (!action)
                return;

            // If the action isn't a function, it should be the name of a method of the view
            if (!_.isFunction(this.options.action))
                action = this.view[action];

            if (action)
                action.call(this.view, event);
        }
    }, {
        // Static properties

        // Cache a selector for the window
        $window: $(window),

        /** Active instances, in the order in which they should be called */
        listeners: [],

        /** Add a new listener instance */
        addListener: function (instance)
        {
            if (instance.listenerAttached)
                return;

            instance.listenerAttached = true;

            // Iterate through the listeners and try to find one whose priority
            // doesn't outrank this instance's
            var notInserted = _.all(this.listeners, function (listener, index)
            {
                if (instance.priority >= listener.priority)
                {
                    this.listeners.splice(index, 0, instance);
                    return false;
                }

                return true;
            }, this);

            // If a lower priority listener wasn't found, insert the listener at the end
            if (notInserted)
                this.listeners.push(instance);

            // If this is the first listener attach the callbacks
            if (this.listeners.length === 1)
                this.attachResizeCallbacks();
        },

        /** Remove an existing listener instance */
        removeListener: function (instance)
        {
            if (!instance.listenerAttached)
                return;

            instance.listenerAttached = false;

            // Iterate through the listeners until the instance is found
            _.all(this.listeners, function (listener, index)
            {
                if (listener === instance)
                {
                    this.listeners.splice(index, 1);
                    return false;
                }

                return true;
            }, this);

            // If there are no more listeners, remove the callback on the window
            if (this.listeners.length === 0)
                this.removeResizeCallbacks();
        },

        attachResizeCallbacks: function ()
        {
            this.$window.on('resize', this.triggerResizing);
        },

        removeResizeCallbacks: function ()
        {
            this.$window.off('resize', this.triggerResizing);
        },

        /** Do the resizing work for each current listener */
        triggerResizing: function (event)
        {
            _.forEach(this.listeners, function (listener)
            {
                listener.doResize(event);
            });
        }
    });

    // Bind and debounce the resizing callback
    ResizeBehavior.triggerResizing = _.debounce(_.bind(ResizeBehavior.triggerResizing, ResizeBehavior), 500);

    return ResizeBehavior;
});