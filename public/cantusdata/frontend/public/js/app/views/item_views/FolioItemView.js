import Radio from 'backbone.radio';
import Marionette from 'marionette';

var manuscriptChannel = Radio.channel('manuscript');

/**
 * View representing a folio's data.
 * Right now it's just a title.
 */
export default Marionette.ItemView.extend({
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
