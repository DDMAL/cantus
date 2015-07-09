define(["backbone"], function (Backbone)
{
    "use strict";

    return Backbone.Model.extend({
        defaults: {
            field: 'all',
            query: '',
            sortBy: 'folio',
            reverseSort: false
        }
    });
});