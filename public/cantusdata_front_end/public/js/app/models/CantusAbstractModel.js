define(["jquery", "backbone"],
    function($, Backbone) {

        return Backbone.Model.extend
        ({
            initialize: function(url)
            {
                this.url = url;
            }
        });
    }

);