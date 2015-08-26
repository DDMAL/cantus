define(['backbone.radio', 'marionette'],
    function(Radio, Marionette)
    {
        "use strict";

        var manuscriptChannel = Radio.channel('manuscript');

        /**
         * View representing a folio's data.
         * Right now it's just a title.
         */
        return Marionette.ItemView.extend({
            template: "#folio-item-template",

            onShow: function ()
            {
                this.listenTo(manuscriptChannel, 'change:folio', this.render);
            },

            serializeData: function ()
            {
                return {
                    number: manuscriptChannel.request('folio')
                };
            }
        });
    });
