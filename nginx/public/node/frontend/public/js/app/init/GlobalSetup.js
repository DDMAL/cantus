/**
 * Provide general, global configuration.
 */

// Ensure Bootstrap JS runs
import _ from 'underscore';
import Backbone from 'backbone';
import Marionette from 'marionette';

import App from 'App';

// Marionette inspector
if (window.__agent) {
    window.__agent.start(Backbone, Marionette);
}
