define(['marionette', 'jquery', 'underscore'],
    function(Marionette, $, _)
    {

        "use strict";

        /**
         * Controller for the popover which contains a manuscript description. Its
         * primary function is to maintain some height invariants which can't be
         * adequately set with CSS.
         *
         * This view relies on being initialized with an `el` parameter set to the
         * popover element.
         */
        return Marionette.View.extend({
            ui: {
                popoverContent: '.popover-content',
                manuscriptData: '.manuscript-data'
            },

            initialize: function ()
            {
                // FIXME(wabain): this needs to be more than 500 so that it runs after
                // BrowserResizer, but there should really be a better way of deciding
                // precedence (or, a better way of doing sizing than setting things with
                // JS...)
                this.resizeCb = _.debounce(_.bind(this.setHeight, this), 600);

                // Cache jQuery selector
                this.$window = $(window);
                this.$window.on('resize', this.resizeCb);

                // This is attached to a popover instead of rendered, so we need to manually
                // call the bind function
                this.bindUIElements();
                this.setHeight();
            },

            /** Set the height of the popover so that it will not extend out of the visible view */
            setHeight: function ()
            {
                // Set the height so that the end of the popover will fall at the bottom of the viewport
                // (add some magic padding to get this to work). Note that the actual computed size of
                // the popover can be bound by the min-height/max-height properties.
                this.ui.popoverContent.height(Math.min(
                    document.body.clientHeight - this.ui.popoverContent.offset().top - 20,
                    this.ui.manuscriptData.height()));

            },

            onDestroy: function()
            {
                this.$window.off('resize', this.resizeCb);
            }
        });
    });
