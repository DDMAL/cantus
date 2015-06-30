define(["models/Manuscript", "collections/CantusAbstractCollection"],
    function(Manuscript, CantusAbstractCollection) {

        'use strict';

        return CantusAbstractCollection.extend
        ({
            model: Manuscript
        });
    });