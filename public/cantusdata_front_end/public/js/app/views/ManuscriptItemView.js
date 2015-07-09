define(["marionette"], function (Marionette)
{
    return Marionette.ItemView.extend({
        template: '#manuscript-item-template',
        tagName: 'li'
    });
});