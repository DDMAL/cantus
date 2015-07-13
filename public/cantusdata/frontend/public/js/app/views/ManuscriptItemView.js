define(["marionette"], function (Marionette)
{
    "use strict";

    return Marionette.ItemView.extend({
        template: '#manuscript-item-template',
        tagName: 'li'
    });
});