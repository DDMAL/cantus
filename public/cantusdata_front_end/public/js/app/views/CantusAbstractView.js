define( ['App', 'backbone', 'marionette', 'jquery'],
    function(App, Backbone, Marionette, $, template) {

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

//        unAssign : function (view, selector) {
//            $(selector).empty();
//        }
        });
    });