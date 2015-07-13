//var CantusAbstractModel = require(["./models/CantusAbstractModel"]);

define(["models/CantusAbstractModel"],
    function(CantusAbstractModel)
    {

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