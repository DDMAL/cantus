//var Chant = require(["models/Chant"]);
//var CantusAbstractCollection = require(["collections/CantusAbstractCollection"]);

define(["jquery","backbone",
        "models/Chant", "collections/CantusAbstractCollection"],
    function($, Backbone, Chant, CantusAbstractCollection) {

        return CantusAbstractCollection.extend
        ({
            model: Chant
        });
    });