//var CantusAbstractModel = require(["models/CantusAbstractModel"]);

define(["jquery", "backbone", "models/CantusAbstractModel"],
    function($, Backbone, CantusAbstractModel) {

        return CantusAbstractModel.extend
        ({
            //defaults: function()
            //{
            //    return {
            //        url: "#",
            //        name: "Test Name",
            //        siglum: "Test Siglum",
            //        siglum_slug: "#",
            //        date: "Tomorrow",
            //        provenance: "Test provenance",
            //        description: "This is a nice manuscript...",
            //        chant_count: 5
            //    };
            //}
        });
    }

);