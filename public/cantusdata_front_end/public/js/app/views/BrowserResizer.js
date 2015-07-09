define(["jquery", "backbone", "singletons/GlobalEventHandler"],
    function($, Backbone, GlobalEventHandler)
    {

        "use strict";

        /**
         * This object handles resizing the browser
         *
         *
         * @constructor
         */
        return Backbone.View.extend
        ({

            divaFullScreen: null,

            initialize: function()
            {
                _.bindAll(this, 'setAll', 'getBaseHeight',
                    'setManuscriptContentContainerHeight', 'setDivaSize',
                    'setDivaFullScreen', 'setViewPortSize');

                // Create a debounced function to alert Diva that its panel size
                // has changed
                this.publishDivaPanelResizedEvent = _.debounce(function ()
                {
                    diva.Events.publish("PanelSizeDidChange");
                }, 500);

                var debouncedSetAll = _.debounce(this.setAll, 500);

                $(window).resize(function()
                {
                    debouncedSetAll();
                });

                this.divaFullScreen = "lol";
                this.listenTo(GlobalEventHandler, "renderView", debouncedSetAll);
                this.listenTo(GlobalEventHandler, "divaFullScreen", function()
                {
                    this.setDivaFullScreen(true);
                });
                this.listenTo(GlobalEventHandler, "divaNotFullScreen", function()
                {
                    this.setDivaFullScreen(false);
                });

                // We also want to do stuff when the viewport is rotated
                this.listenTo($(window), "orientationchange", this.setViewPortSize);
            },

            setAll: function()
            {
                var baseHeight = this.getBaseHeight();

                this.setManuscriptContentContainerHeight(baseHeight);
                this.setDivaSize(baseHeight);
                this.setViewPortSize();
            },

            /** Get the base height to compute the height of other elements against.
             * This corresponds to all the space in the viewport which isn't taken
             * up by the header. */
            getBaseHeight: function ()
            {
                return $(window).height() - $("#header-container").height();
            },

            setManuscriptContentContainerHeight: function(baseHeight)
            {
                $('#manuscript-data-container').css("height",
                        baseHeight -
                            $("#manuscript-title-container").height() -
                            $("#manuscript-nav-container").height());
            },

            /**
             * Recalculate and set the new size of the Diva viewer.
             */
            setDivaSize: function(baseHeight)
            {
                if (this.divaFullScreen !== true)
                {
                    $('.diva-outer').css("height", baseHeight - 75);

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
                    var windowWidth = $(window).width();
                    var windowHeight = $(window).height();
                    var computedHeight = 880 * (windowHeight / windowWidth);
                    var zoomFactor = 880 / windowWidth;
                    $('meta[name=viewport]').attr('content',
                        'width=880, height=' + computedHeight + 'initial-scale=' + zoomFactor + ', user-scalable=no');
                }
                else
                {
                    // Big screens
                    $('meta[name=viewport]').attr('content', 'width=device-width');
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
                this.setDivaSize(this.getBaseHeight());
            }
        });
    }

);