define(["backbone", "config/GlobalVars"],
    function(Backbone, GlobalVars)
    {

        "use strict";

        return Backbone.Model.extend({
            // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

            defaults:  {
                url: "#",
                name: "Test Name",
                siglum: "Test Siglum",
                siglum_slug: "#",
                date: "Tomorrow",
                provenance: "Test provenance",
                description: "This is a nice manuscript...",
                chant_count: 5
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