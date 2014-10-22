define(["jquery", "backbone"],
    function($, Backbone) {

        "use strict";

        /**
         * An object that acts like a big row of switches.  You can call
         * getValue() to get the index of the first true element.
         */
        return Backbone.Model.extend
        ({

            length: 0,
            valueArray: undefined,

            initialize: function(length)
            {
                this.valueArray = [];
                this.length = parseInt(length, 10);
                for (var i = 0; i < this.length; i++)
                {
                    this.valueArray.push(false);
                }
            },

            /**
             * Set a value.
             *
             * @param index int
             * @param value boolean
             */
            setValue: function(index, value)
            {
                // Handle out-of-bounds cases
                if (index < 0)
                {
                    index = 0;
                }
                else if (index >= this.length)
                {
                    index = this.length - 1;
                }
                // Set the value
                this.valueArray[index] = value;
            },

            /**
             * Return the index of the true element.
             *
             * @returns {*}
             */
            getValue: function()
            {
                for (var i = 0; i < this.length; i++)
                {
                    if (this.valueArray[i] === true)
                    {
                        return i;
                    }
                }
                // No elements are true!
                return undefined;
            }
        });
    }

);