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

            initialize: function()
            {
                _.bindAll(this, 'setAll', 'setContainerHeight', 'setScrollableHeight',
                    'setManuscriptContentContainerHeight', 'setDivaSize',
                    'setDivaFullScreen', 'setViewPortSize');

                // Create a debounced function to alert Diva that its panel size
                // has changed
                this.publishDivaPanelResizedEvent = _.debounce(function () {
                    diva.Events.publish("PanelSizeDidChange");
                }, 500);

                var debouncedSetAll = _.debounce(this.setAll, 500);

                $(window).resize(function()
                {
                    debouncedSetAll();
                });

                this.divaFullScreen = "lol";
                this.listenTo(GlobalEventHandler, "renderView", debouncedSetAll);
                this.listenTo(GlobalEventHandler, "divaFullScreen",
                    function(){this.setDivaFullScreen(true);});
                this.listenTo(GlobalEventHandler, "divaNotFullScreen",
                    function(){this.setDivaFullScreen(false);});

                // We also want to do stuff when the viewport is rotated
                this.listenTo($(window), "orientationchange", this.setViewPortSize);
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

            /**
             * Recalculate and set the new size of the Diva viewer.
             */
            setDivaSize: function()
            {
                if (this.divaFullScreen !== true)
                {
                    $('.diva-outer').css("height",
                            $("#content-container").height() - 75);

                    var divaData = $('#diva-wrapper').data('diva');
                    if (divaData !== undefined)
                    {
                        // Only try to resize diva if diva exists
                        // Include a delay so that we don't have repeats
                        this.publishDivaPanelResizedEvent();
                    }
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