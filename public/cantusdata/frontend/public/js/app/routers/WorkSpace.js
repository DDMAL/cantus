define(["backbone", "marionette"],
    function(Backbone, Marionette)
    {

    "use strict";

    return Marionette.AppRouter.extend({
        appRoutes: {
            "": "manuscripts",
            "manuscript/:query/?folio=(:folio)&chant=(:chant)": "manuscriptSingle",
            "manuscript/:query/?folio=(:folio)": "manuscriptSingle",
            "manuscript/:query/": "manuscriptSingle",
            "manuscripts/": "manuscripts",
            "search/?q=(:query)": "search",
            "search/": "search",
            '*path': "notFound"
        }
    });
});