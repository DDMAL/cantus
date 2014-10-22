//var Manuscript = require(["models/Manuscript"]);
//var CantusAbstractCollection = require(["collections/CantusAbstractCollection"]);

define(["jquery","backbone", "models/Manuscript", "collections/CantusAbstractCollection"],
    function($, Backbone, Manuscript, CantusAbstractCollection) {
        return CantusAbstractCollection.extend
        ({
            model: Manuscript
        });
    });