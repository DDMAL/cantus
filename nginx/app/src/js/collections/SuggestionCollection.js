import Backbone from 'backbone';
import GlobalVars from 'config/GlobalVars';

import Suggestion from 'models/Suggestion';

export default Backbone.Collection.extend({

    model: Suggestion,

    baseUrl: function()
    {
        return GlobalVars.siteUrl + 'suggest/';
    },

    parse: function(data)
    {
        return data;
    }
});
