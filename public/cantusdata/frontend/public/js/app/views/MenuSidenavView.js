define([
    "underscore",
    "jquery",
    "marionette",
    "backbone.radio",
    "singletons/NavigationManager"
], function (_, $, Marionette, Radio, NavigationManager)
{
    "use strict";

    var sidenavChannel = Radio.channel('sidenav');

    /**
     * View for the primary navigation menu
     */
    return Marionette.CompositeView.extend({
        template: '#menu-sidenav-template',

        childViewContainer: '.sidenav ul',

        childView: Marionette.ItemView.extend({
            tagName: 'li',
            template: '#menu-sidenav-item-template',

            events: {
                click: function (event)
                {
                    if (!event.defaultPrevented)
                    {
                        sidenavChannel.request('collapse');
                    }
                }
            },

            templateHelpers: {
                serializeAttributes: function (attr)
                {
                    return _.map(attr, function (val, key)
                    {
                        return key + '="' + _.escape(val) + '"';
                    }).join(' ');
                }
            }
        }),

        ui: {
            sidenav: '.sidenav'
        },

        initialize: function ()
        {
            // Use the nav items sent to the navigation manager
            this.collection = NavigationManager.navItems;
            this.isExpanded = this.backdrop = null;
        },

        onRender: function ()
        {
            this.isExpanded = this.ui.sidenav.hasClass('in');

            sidenavChannel.reply('toggle', this.toggle, this);
            sidenavChannel.reply('expand', this.expand, this);
            sidenavChannel.reply('collapse', this.collapse, this);
        },

        onDestroy: function ()
        {
            // Stop replying to all requests where `this` is the context
            sidenavChannel.stopReplying(null, null, this);
        },

        /** Toggle the side nav open or closed */
        toggle: function ()
        {
            this[this.isExpanded ? 'collapse' : 'expand']();
        },

        /** Expand the side nav */
        expand: function ()
        {
            if (this.isExpanded)
                return;

            this.isExpanded = true;

            if (!this.backdrop)
            {
                this.backdrop = $('<div class="sidenav-backdrop fade">');
                this.backdrop.on('click', _.bind(this.collapse, this));
            }

            this.backdrop.appendTo(document.body);
            this.ui.sidenav.addClass('sliding');

            // Force a reflow
            // The logic here follows Bootstrap's very closely
            this.backdrop[0].offsetWidth; // jshint ignore:line

            this.backdrop.addClass('in');
            this.ui.sidenav.addClass('in');
            this.ui.sidenav.removeClass('sliding');
        },

        /** Collapse the side nav */
        collapse: function ()
        {
            if (!this.isExpanded)
                return;

            this.isExpanded = false;

            this.ui.sidenav.addClass('sliding');

            this.ui.sidenav.removeClass('in');
            this.afterTransition(this.backdrop, 300, function ()
            {
                this.ui.sidenav.removeClass('sliding');
            });

            this.backdrop.removeClass('in');
            this.afterTransition(this.backdrop, 150, function ()
            {
                this.backdrop.remove();
                this.backdrop = null;
            });
        },

        /**
         * Call the callback function after the transitions for the element have completed,
         * or after the given number of milliseconds have elapsed if it is not possible
         * to detect the transition end.
         *
         * @param {jQuery} jqElem
         * @param {number} fallbackMs
         * @param {function} callback Called with the view as the context
         */
        afterTransition: function (jqElem, fallbackMs, callback)
        {
            // These jQuery properties are defined by Bootstrap
            jqElem
                .one($.support.transition.end, _.bind(callback, this))
                .emulateTransitionEnd(fallbackMs);
        }
    });
});