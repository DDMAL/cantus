import Radio from 'backbone.radio';
import Marionette from 'marionette';

import template from './nav-folio-number.template.html';

var manuscriptChannel = Radio.channel('manuscript');
var folioChannel = Radio.channel('folio');


export default Marionette.ItemView.extend({
    template,

    tagName: 'span',

    onShow: function ()
    {
        this.listenTo(folioChannel, 'folioLoaded', this.render);
    },

    serializeData: function ()
    {
        return {
            number: manuscriptChannel.request('pageAlias')
        }
    }
});
