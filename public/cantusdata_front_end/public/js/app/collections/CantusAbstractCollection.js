define(["backbone"],
    function(Backbone)
    {

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