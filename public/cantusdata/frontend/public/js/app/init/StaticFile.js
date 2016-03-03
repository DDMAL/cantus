import "init/BackboneCustomization";
import "jquery";
import "backbone";
import "marionette";
import "bootstrap";

import _ from "underscore";
import App from "App";
import ResizeBehavior from "behaviors/ResizeBehavior";
import NavigationManager from "singletons/NavigationManager";

// Needed for the search view
_.extend(App.behaviors, {
    resize: ResizeBehavior
});

App.on('start', function ()
{
    var titleElem = document.getElementsByTagName('h1')[0];

    // If this is not the root page of the application, display additional
    // titling besides "Cantus Ultimus"
    if (titleElem && window.location.pathname !== '/')
        NavigationManager.registerPage({navbarTitle: titleElem.textContent});
    else
        NavigationManager.registerPage({});
});

App.start();
