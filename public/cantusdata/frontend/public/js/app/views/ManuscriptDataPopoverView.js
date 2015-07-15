define(['marionette'],
    function(Marionette)
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

            behaviors: {
                resize: {
                    target: false,
                    action: 'setHeight',

                    // Run later than the Diva and manuscript detail views
                    priority: 500
                }
            },

            initialize: function ()
            {
                // This is attached directly to a popover rather than being rendered, so we need to manually
                // call the bind function and trigger appropriate lifecycle events
                this.bindUIElements();
                this.triggerMethod('render');
                this.triggerMethod('show');
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

            }
        });
    });
