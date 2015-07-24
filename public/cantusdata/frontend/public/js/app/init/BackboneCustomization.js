/**
 * Provide general, global configuration for Backbone and Marionette.
 */
define([
    'underscore',
    'App',
    'backbone',
    'marionette',
    'templates'
], function (_, App, Backbone, Marionette, templates)
{
    "use strict";

    /**
     * Load the pre-compiled template from the template store.
     *
     * This monkey patching is the recommended way of customizing Marionette template loading.
     *
     * @param {string} templateId
     * @returns {Function}
     */
    Marionette.TemplateCache.prototype.loadTemplate = function (templateId)
    {
        var templateFile = templateId.replace(/^#/, '') + '.html';

        if (!templates.hasOwnProperty(templateFile))
        {
            var err = new Error('Could not find template: "' + templateId + '" (' + templateFile + ')');
            err.name = 'NoTemplateError';

            throw err;
        }

        return templates[templateFile];
    };

    /** Return the pre-compiled template untouched. */
    Marionette.TemplateCache.prototype.compileTemplate = _.identity;

    Marionette.Behaviors.behaviorsLookup = _.constant(App.behaviors);
});
