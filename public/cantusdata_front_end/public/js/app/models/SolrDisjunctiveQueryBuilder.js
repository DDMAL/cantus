define(["jquery", "backbone"],
    function($, Backbone) {

        "use strict";

        return Backbone.Model.extend
        ({
            field: undefined,
            values: undefined,

            initialize: function(field, values)
            {
                this.field = String(field);
                this.values = [];
                for (var i = 0; i < values.length; i++)
                {
                    this.addValue(values[i]);
                }
            },

            /**
             * Add a value to the disjunctive query.
             *
             * @param value
             */
            addValue: function(value)
            {
                this.values.push(String(value));
            },

            /**
             * Construct the query.
             *
             * @returns {string}
             */
            getQuery: function()
            {
                var output = this.field + ": (";

                if (this.values.length > 0)
                {
                    // The first value
                    output += ('"' + this.values[0] + '"');
                    // The rest
                    for (var i = 1; i < this.values.length; i++)
                    {
                        output += (' OR "' + this.values[i] + '"');
                    }
                }

                return output + ")";
            }
        });
    }

);