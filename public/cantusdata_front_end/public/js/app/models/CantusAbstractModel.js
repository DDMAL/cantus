define(["jquery", "backbone"],
    function($, Backbone)
    {

        "use strict";

        return Backbone.Model.extend
        ({
            initialize: function(url)
            {
                this.url = url;
            }
        });
    }

);