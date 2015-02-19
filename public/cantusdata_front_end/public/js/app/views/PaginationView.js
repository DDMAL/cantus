define( ['App', 'backbone', 'marionette', 'jquery',
        "views/CantusAbstractView",
        "singletons/GlobalEventHandler"],
    function(App, Backbone, Marionette, $,
             CantusAbstractView,
             GlobalEventHandler,
             template) {

        "use strict";

        /**
         * A simple paginator that fires events when it changes page.
         * Page indexes start at 1.
         *
         * @type {*|void}
         */
        return CantusAbstractView.extend
        ({
            elementCount: 1,
            pageCount: 1,
            pageSize: 10,

            // Used for rendering
            currentPage: 1,
            startPage: 1,
            endPage: 1,
            maxWidth: 9,

            events: {},

            initialize: function(options)
            {
                _.bindAll(this, 'render', 'setPage', 'increment', 'decrement',
                    'render', 'buttonClick');
                this.template = _.template($('#pagination-template').html());

                this.setParams(options.elementCount,
                    options.pageSize, options.currentPage);
            },

            /**
             * Set the paginator params.  Equivalent to re-construction.
             *
             * @param elementCount
             * @param pageSize
             * @param currentPage
             */
            setParams: function(elementCount, pageSize, currentPage)
            {
                // Set the size and the current
                this.elementCount = elementCount;
                this.pageSize = pageSize;
                // Calculate number of pages
                this.pageCount = Math.floor(this.elementCount / this.pageSize);
                if (this.elementCount % this.pageSize !== 0)
                {
                    this.pageCount++;
                }
                // Calculate number of pages
                this.setPage(currentPage);
            },

            /**
             * Register the events that are necessary to have clickable buttons.
             */
            registerEvents: function()
            {
                // Clear out the events
                this.events = {};
                // No binding if there are no elements
                if (this.elementCount === 0)
                {
                    return;
                }
                // Backwards
                if (this.currentPage > 1)
                {
                    this.events["click .page-back"] = "decrement";
                }
                // Forwards
                if (this.currentPage < this.pageCount)
                {
                    this.events["click .page-forward"] = "increment";
                }
                // Add the page clickers
                for (var i = this.startPage; i <= this.endPage; i++)
                {
                    if (i !== this.currentPage)
                    {
                        this.events["click .page-" + i] = "buttonClick";
                    }
                }
                // Delegate the new events
                this.delegateEvents();
            },

            /**
             * Get the current paginator page.
             *
             * @returns {number} 1 to infinity
             */
            getPage: function()
            {
                return this.currentPage;
            },

            /**
             * Set the page and render.
             *
             * @param page integer
             */
            setPage: function(page)
            {
                if (page < 1)
                {
                    this.currentPage = 1;
                }
                else if (page > this.pageCount)
                {
                    this.currentPage = this.pageCount;
                }
                else
                {
                    this.currentPage = page;
                }

                if (this.pageCount <= this.maxWidth)
                {
                    // This is the case where we don't need to scroll through
                    // more pages than can fit in the paginator.
                    this.startPage = 1;
                    this.endPage = this.pageCount;
                }
                else
                {
                    // This is the case where there are more pages than can fit
                    // In the paginator, so we need to "scroll" through the numbers.
                    if (this.currentPage <= Math.floor(((this.maxWidth | 0) / 2)))
                    {
                        // This is the case of the first few numbers
                        this.startPage = 1;
                        this.endPage = this.maxWidth;
                    }
                    else if ((this.pageCount - this.currentPage) <= Math.floor((this.maxWidth | 0) / 2))
                    {
                        // This is the case of the last few numbers
                        this.startPage = this.pageCount - this.maxWidth + 1;
                        this.endPage = this.pageCount;
                    }
                    else
                    {
                        // This case should capture most instances where the
                        // current page is somewhere in the "middle" of the paginator"
                        this.startPage = this.currentPage - ((this.maxWidth / 2) | 0);
                        this.endPage = this.currentPage + ((this.maxWidth / 2) | 0);
                    }
                }

                this.render();
                // We have to register the events every time we render
                this.registerEvents();
                this.trigger("change", {page: this.getPage()});
            },

            /**
             * Go to the next page.
             */
            increment: function()
            {
                this.setPage(this.currentPage + 1);
            },

            /**
             * Go to the previous page.
             */
            decrement: function()
            {
                this.setPage(this.currentPage - 1);
            },

            /**
             * This function gets called when you click on one of the numbered
             * paginator buttons.
             *
             * @param query
             */
            buttonClick: function(query)
            {
                var buttonId = query.target.className;
                var newPage = parseInt(buttonId.split("page-")[1], 10);
                this.setPage(newPage);
            },

            render: function()
            {
                $(this.el).html(this.template(
                    {
                        startPage: this.startPage,
                        endPage: this.endPage,
                        currentPage: this.currentPage
                    }
                ));
                GlobalEventHandler.trigger("renderView");
                return this.trigger('render', this);
            }
        });
    });