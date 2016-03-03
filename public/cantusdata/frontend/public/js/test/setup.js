// Initialization
import 'init/BackboneCustomization';
import App from 'App';
import ResizeBehavior from 'behaviors/ResizeBehavior';

App.behaviors.resize = ResizeBehavior;

// Test scaffolding
import Marionette from 'marionette';
import $ from 'jquery';

var testView = null;

module.exports.showView = function (view)
{
    if (testView === null)
    {
        var testParent = $('<div id="test-wrapper"><div id="test"></div></div>');
        $(document.body).append(testParent);

        testView = new Marionette.LayoutView({
            el: testParent,
            regions: {
                testRegion: '#test'
            }
        });
    }
    else if (testView.testRegion.currentView)
    {
        var err = new Error('Expected the test region to be empty');
        err.name = 'TestSetupError';

        throw err;
    }

    testView.testRegion.show(view);
};

module.exports.clearView = function ()
{
    if (testView)
        testView.testRegion.empty();
};
