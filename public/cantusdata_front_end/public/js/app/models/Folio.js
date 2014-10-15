//var CantusAbstractModel = require(["./models/CantusAbstractModel"]);

define(["jquery", "backbone", "models/CantusAbstractModel"],
    function($, Backbone, CantusAbstractModel) {

        return CantusAbstractModel.extend
        ({
            //defaults: function()
            //{
            //    return {
            //        number: "000",
            //        manuscript: null,
            //        chant_count: 0,
            //        chant_set: []
            //    }
            //}
        });
    }

);