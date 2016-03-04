import Marionette from 'marionette';
import RootView from 'layout/RootView';

var App = new Marionette.Application({
    behaviors: {},

    onBeforeStart: function ()
    {
        // Instantiate the root view
        this.rootView = new RootView();
        this.rootView.render();
    }
});

export default App;
