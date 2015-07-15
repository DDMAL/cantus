define(["backbone", "models/Chant"], function(Backbone, Chant)
{
    'use strict';

    return Backbone.Collection.extend({
        model: Chant
    });
});