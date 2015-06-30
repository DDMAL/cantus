// Include Desktop Specific JavaScript files here (or inside of your Desktop Controller, or differentiate based off App.mobile === false)
require(["App", "routers/WorkSpace", "jquery", "backbone", "marionette", "bootstrap"],
    function (App, WorkSpace) {

        "use strict";

        App.appRouter = new WorkSpace({
//            controller:new AppController()
        });
        // Start Marionette Application in desktop mode (default)
        App.start();

    });