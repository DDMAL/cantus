//var CantusAbstractModel = require(["./models/CantusAbstractModel"]);

define(["jquery", "backbone", "models/CantusAbstractModel"],
    function($, Backbone, CantusAbstractModel) {

        "use strict";

        return CantusAbstractModel.extend
        ({
            //defaults: function()
            //{
            //    return {
            //        marginalia: "the marginalia",
            //        folio: "the folio",
            //        sequence:"the sequence",
            //        cantus_id: "the cantus id",
            //        feast: "the feast",
            //        office: "the office",
            //        genre: "the genre",
            //        lit_position: "the lit position",
            //        mode: "the mode",
            //        differentia: "the differentia",
            //        finalis: "the finalis",
            //        incipit: "the incipit",
            //        full_text: "Quite a nice chant!",
            //        concordances: [],
            //        volpiano: "the volpiano",
            //        manuscript: "the manuscript"
            //    }
            //}
        });
    }

);