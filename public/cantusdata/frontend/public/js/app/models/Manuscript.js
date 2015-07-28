define(["backbone", "config/GlobalVars"],
    function(Backbone, GlobalVars)
    {

        "use strict";

        return Backbone.Model.extend({
            // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

            defaults:  {
                name: null,
                siglum: null,
                siglum_slug: null,
                date: null,
                provenance: null,
                description: null,
                chant_count: null
            },

            // jscs:enable

            url: function ()
            {
                // jshint eqnull: true
                if (this.id == null)
                    return null;

                return GlobalVars.siteUrl + "manuscript/" + this.id + "/";
            },

            /**
             * Check if a particular plugin is activated for this manuscript.
             *
             * @param pluginName
             * @returns {boolean}
             */
            isPluginActivated: function(pluginName)
            {
                // Grab the plugin array
                var plugins = this.get("plugins");
                // Check if the plugin is activated
                return plugins.indexOf(String(pluginName)) > -1;
            }
        });
    }
);