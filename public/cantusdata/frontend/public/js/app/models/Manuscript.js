//var CantusAbstractModel = require(["models/CantusAbstractModel"]);

define(["models/CantusAbstractModel"],
    function(CantusAbstractModel)
    {

        "use strict";

        return CantusAbstractModel.extend
        ({
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