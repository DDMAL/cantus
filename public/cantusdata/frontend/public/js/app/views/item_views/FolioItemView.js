define(['marionette'],
    function(Marionette)
    {

        "use strict";

        /**
         * View representing a folio's data.
         * Right now it's just a title.
         */
        return Marionette.ItemView.extend({
            template: "#folio-item-template",
            tagName: 'h3',

            modelEvents:
            {
                "change": "render"
            }
        });
    });
