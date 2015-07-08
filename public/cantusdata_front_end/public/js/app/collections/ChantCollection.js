define(["models/Chant", "collections/CantusAbstractCollection"],
    function(Chant, CantusAbstractCollection)
    {

        'use strict';

        return CantusAbstractCollection.extend
        ({
            model: Chant
        });
    });