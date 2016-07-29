import Backbone from "backbone";
import GlobalVars from "config/GlobalVars";

export default Backbone.Model.extend({
    // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

    defaults:  {
        name: null,
        siglum: null,
        siglum_slug: null,
        date: null,
        provenance: null,
        description: null,
        folio_count: null,
        chant_count: null,
        cantus_url: null,
        manifest_url: null
    },

    // jscs:enable

    url: function ()
    {
        if (this.id == null) // eslint-disable-line eqeqeq
            return null;

        return GlobalVars.siteUrl + "manuscript/" + this.id + "/";
    },

    /**
     * Check if a particular plugin is activated for this manuscript.
     *
     * @param pluginName
     * @returns {boolean}
     */
    isPluginActivated: function (pluginName)
    {
        // Grab the plugin array
        var plugins = this.get("plugins");
        // Check if the plugin is activated
        return plugins.indexOf(pluginName) > -1;
    }
});
