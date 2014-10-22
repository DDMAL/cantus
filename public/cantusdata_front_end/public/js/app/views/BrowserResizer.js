define(["jquery", "backbone", "singletons/GlobalEventHandler"],
    function($, Backbone, GlobalEventHandler) {

        "use strict";

        /**
         * This object handles resizing the browser
         *
         *
         * @type {{setContainerHeight: setContainerHeight, setScrollableHeight: setScrollableHeight, setManuscriptContentContainerHeight: setManuscriptContentContainerHeight, setDivaHeight: setDivaHeight}}
         */
        return Backbone.View.extend
        ({

            divaFullScreen: null,
            timedQuery: null,

            initialize: function()
            {
                _.bindAll(this, 'timedQuerySetAll', 'setAll', 'setContainerHeight',
                    'setScrollableHeight', 'setManuscriptContentContainerHeight',
                    'setDivaSize', 'setDivaFullScreen', 'setViewPortSize');
                var self = this;
                $(window).resize(function()
                {
                    self.timedQuerySetAll();
                });
                this.divaFullScreen = "lol";
                this.listenTo(GlobalEventHandler, "renderView",
                    this.timedQuerySetAll);
                this.listenTo(GlobalEventHandler, "divaFullScreen",
                    function(){this.setDivaFullScreen(true);});
                this.listenTo(GlobalEventHandler, "divaNotFullScreen",
                    function(){this.setDivaFullScreen(false);});

                // We also want to do stuff when the viewport is rotated
                this.listenTo($(window), "orientationchange", this.setViewPortSize);
            },

            /**
             * Set a timed query for resizing the window.
             */
            timedQuerySetAll: function()
            {
                window.clearTimeout(this.timedQuery);
                this.timedQuery = window.setTimeout(this.setAll, 250);
            },

            setAll: function()
            {
                this.setContainerHeight();
                this.setManuscriptContentContainerHeight();
                this.setDivaSize();
                this.setViewPortSize();
            },

            setContainerHeight: function()
            {
                $('#content-container').css("height",
                        $(window).height() - $("#header-container").height());
            },

            setScrollableHeight: function()
            {
                $('.scrollable').css("height", $("#content-container").height());
            },

            setManuscriptContentContainerHeight: function()
            {
                $('#manuscript-data-container').css("height",
                        $("#content-container").height() - $("#manuscript-title-container").height());
            },

            setDivaSize: function()
            {
                if (this.divaFullScreen !== true)
                {
                    $('.diva-outer').css("height",
                            $("#content-container").height() - 75);
                }
            },

            setViewPortSize: function()
            {
                if ($(window).width() <= 880)
                {
                    // Small screens
                    var window_width = $(window).width();
                    var window_height = $(window).height();
                    var computed_height = 880 * (window_height / window_width);
                    var zoom_factor = 880 / window_width;
                    $('meta[name=viewport]').attr('content','width=880, height=' + computed_height + 'initial-scale=' + zoom_factor + ', user-scalable=no');
                }
                else
                {
                    // Big screens
                    $('meta[name=viewport]').attr('content','width=device-width');
                }
            },

            /**
             * Resize the Diva viewer into fullscreen mode when necessary
             *
             * @param isFullScreen
             */
            setDivaFullScreen: function(isFullScreen)
            {
                if (isFullScreen === true)
                {
                    this.divaFullScreen = true;
                }
                else if (isFullScreen === false)
                {
                    this.divaFullScreen = false;
                }
                this.setDivaSize();
            }
        });
    }

);