import Marionette from "marionette";

export default Marionette.AppRouter.extend({
    appRoutes: {
        "manuscript/:id/": "manuscriptSingle",
        "manuscripts/": "manuscripts",
        "search/": "search",
        '*path': "notFound"
    }
});
