/**
 * Provide general, global configuration.
 */

import _ from 'underscore';
import Backbone from 'backbone';
import Marionette from 'marionette';
import bootstrap from 'bootstrap';

// Marionette inspector
if (window.__agent) {
    window.__agent.start(Backbone, Marionette);
}
