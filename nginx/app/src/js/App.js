import Marionette from 'marionette';
import RootView from 'layout/RootView';


var App = new Marionette.Application({

    onBeforeStart: function () {
        // Instantiate the root view
        this.rootView = new RootView();
    }
});

export default App;
