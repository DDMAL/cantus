import "init/BackboneCustomization";
import "jquery";
import "underscore";
import "backbone";
import "marionette";
import "bootstrap";
import "modernizr";

import App from "App";
import NavigationManager from "singletons/NavigationManager";

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
