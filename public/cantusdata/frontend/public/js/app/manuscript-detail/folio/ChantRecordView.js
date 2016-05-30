import Marionette from 'marionette';

import { parseVolpianoSyllables } from 'utils/VolpianoDisplayHelper';

import template from './chant-record.template.html';

export default Marionette.ItemView.extend({
    template,

    initialize: function()
    {
        // Add a text underlay to the volpiano
        var volpiano = this.model.get('volpiano');
        var text = this.model.get('full_text');
        var formattedVolpiano = parseVolpianoSyllables(text, volpiano);
        this.model.set('volpiano', formattedVolpiano);
    }
});
