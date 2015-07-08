define(["views/SearchView"],
    function(SearchView)
    {

        'use strict';

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