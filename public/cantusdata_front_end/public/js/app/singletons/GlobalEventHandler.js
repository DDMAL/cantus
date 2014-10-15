define(['backbone', 'underscore'],
    function (Backbone, _) {

    // Global Event Handler for global events
    var singleton = function () {
        var globalEventHandler = {};
        _.extend(globalEventHandler, Backbone.Events);

        return globalEventHandler;
    };
    return singleton();
});