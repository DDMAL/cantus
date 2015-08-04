define(["backbone", "marionette"],
    function(Backbone, Marionette)
    {

    "use strict";

    return Marionette.AppRouter.extend({
        appRoutes: {
            "manuscript/:id/": "manuscriptSingle",
            "manuscripts/": "manuscripts",
            "search/": "search",
            '*path': "notFound"
        }
    });
});