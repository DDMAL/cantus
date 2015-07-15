define(["backbone", "models/Manuscript"], function(Backbone, Manuscript)
{
    'use strict';

    return Backbone.Collection.extend({
        model: Manuscript
    });
});