var SearchView = require(["views/SearchView"]);

define( ['App', 'backbone', 'marionette', 'jquery', "views/SearchView"],
    function(App, Backbone, Marionette, $, SearchView, template) {

        /**
         * A special kind of search that exists within some particular manuscript.
         */
        return SearchView.extend
        (
            {
                showManuscriptName: false
            }
        );
    });