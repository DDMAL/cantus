import Radio from 'backbone.radio';
import Marionette from 'marionette';

import template from './nav-folio-number.template.html';

var manuscriptChannel = Radio.channel('manuscript');


export default Marionette.ItemView.extend({
    template,

    tagName: 'span',

    onShow: function ()
    {
        this.listenTo(manuscriptChannel, 'change:folio', this.render);
    },

    serializeData: function ()
    {
        return {
            number: String(manuscriptChannel.request('folio')).split(",").join(", ")
        };
    }
});
