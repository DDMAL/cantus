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
        chant_count: null
    },

    // jscs:enable

    // Map to the Cantus URLs for the various manuscripts, since we don't
    // have any other way of getting them.
    // Let this be a warning about the danger of non-meaningful URLs, I guess.
    _cantusUrls: {
        'cdn-hsmu-m2149l4': 'http://cantus.uwaterloo.ca/source/123723',
        'ch-sgs-390': 'http://cantus.uwaterloo.ca/source/123717',
        'ch-sgs-391': 'http://cantus.uwaterloo.ca/source/123718',
        'nl-uu-406': 'http://cantus.uwaterloo.ca/source/123641'
    },

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
    },

    /**
     * Get the URL for this manuscript in the Cantus database,
     * if it is known
     */
    getCantusUrl: function ()
    {
        return this._cantusUrls[this.get('siglum_slug')] || null;
    }
});
