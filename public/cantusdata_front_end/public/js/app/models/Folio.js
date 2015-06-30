//var CantusAbstractModel = require(["./models/CantusAbstractModel"]);

define(["jquery", "backbone", "models/CantusAbstractModel"],
    function($, Backbone, CantusAbstractModel) {

        "use strict";

        return CantusAbstractModel.extend
        ({
            defaults: function()
            {
                return {
                    number: "000"
                };
            }
        });
    }

);