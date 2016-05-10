import Marionette from 'marionette';

import DivaFolioAdvancerView from "./DivaFolioAdvancerView";

import template from './toolbar.template.html';

export default Marionette.LayoutView.extend({
    template,

    regions: {
        divaFolioAdvancerRegion: '.diva-folio-advancer-region'
    },

    onShow: function()
    {
        this.divaFolioAdvancerRegion.show(new DivaFolioAdvancerView());
    }

});