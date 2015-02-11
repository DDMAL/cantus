define( ['App', 'backbone', 'marionette', 'jquery', "views/SearchView"],
    function(App, Backbone, Marionette, $, SearchView) {

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