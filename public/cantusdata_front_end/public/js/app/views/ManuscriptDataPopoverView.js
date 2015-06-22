define(['backbone', 'marionette', 'jquery', 'underscore', 'GlobalEventHandler'],
    function(Backbone, Marionette, $, _, GlobalEventHandler) {

        "use strict";

        /**
         * This page shows an individual manuscript.  You get a nice diva viewer
         * and you can look through the chant info.
         *
         * @type {*|void}
         */
        return Marionette.ItemView.extend({
            initialize: function ()
            {
                this.resizeCb = _.debounce(_.bind(this, this.setSize), 250);

                // Cache jQuery selectors
                this.$body = $(document.body);
                this.$window = $(window);

                this.$window.on('resize', this.resizeCb);
            },

            setSize: function ()
            {
                // Set height so that the popover will not extend outside the page
                this.$el.height('auto');
                this.$el.height(this.$body.height() - this.$el.height() - this.$el.offset().top);
            },

            onRender: function ()
            {
                this.setSize();
            },

            /**
             * Marionette method called automatically before the destroy event happens.
             */
            onDestroy: function()
            {
                this.$window.off('resize', this.resizeCb);
            }
        });
    });
