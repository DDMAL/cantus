define(["backbone"],
    function(Backbone)
    {
        "use strict";

        return Backbone.Collection.extend
        ({
            initialize: function(url)
            {
                if (url)
                {
                    this.url = url;
                }
            },

            defaults: function()
            {
                return [];
            }
        });
    });