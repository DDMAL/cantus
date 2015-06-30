define( ['App', 'backbone'],
    function(App, Backbone) {

        'use strict';

        return Backbone.View.extend
        ({
            /**
             * Used to render subviews.
             *
             * @param view The view object to be rendered
             * @param selector The html selector where you want to render the view
             */
            assign : function (view, selector) {
                view.setElement(selector).render();
            }
        });
    });