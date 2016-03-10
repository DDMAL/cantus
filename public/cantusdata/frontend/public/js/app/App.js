import Marionette from 'marionette';
import RootView from 'layout/RootView';

import FillViewportHeightBehavior from 'behaviors/FillViewportHeightBehavior';

var App = new Marionette.Application({
    behaviors: {
        fillViewportHeight: FillViewportHeightBehavior
    },

    onBeforeStart: function ()
    {
        // Instantiate the root view
        this.rootView = new RootView();
        this.rootView.render();
    }
});

export default App;
