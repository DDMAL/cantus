/**
 * Provide general, global configuration.
 */

// Ensure Bootstrap JS runs
import "bootstrap";

// Ensure Modernizr runs
import "modernizr";

import _ from 'underscore';
import Backbone from 'backbone';
import Marionette from 'marionette';

import App from 'App';

// Marionette inspector
if (window.__agent)
{
    window.__agent.start(Backbone, Marionette);
}

/**
 * Throw an error if something tries to load a template by ID.
 *
 * This monkey patching is the recommended way of customizing Marionette
 * template loading.
 *
 * @param {string} templateId
 */
Marionette.TemplateCache.prototype.loadTemplate = function (templateId)
{
    throw new Error(`Cannot load template "${templateId}" by ID. Load it via import instead.`);
};

// Set the global behaviors lookup
Marionette.Behaviors.behaviorsLookup = _.constant(App.behaviors);
