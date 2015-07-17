define(["underscore", "jquery", "marionette"], function (_, $, Marionette)
{
    "use strict";

    /**
     * Implements a declarative interface for changing the values of metadata content
     * and global styling in the DOM for the lifetime of a view. Values are set when the
     * view is shown and persist until the view is destroyed. The behavior tries to prevent
     * more than one view from modifying an element concurrently, although currently it
     * checks the selector instead of the element itself.
     *
     * The following snippet would set the document title to "Hello world" when the view
     * was shown and restore the initial value once the view was destroyed. It raises an
     * error if another view also tries to use the behavior to modify the title at the same
     * time.
     *
     *     behaviors: {
     *         headConfig: {
     *             title: {
     *                 text: 'Hello world'
     *             }
     *         }
     *     }
     *
     * @constructor
     */
    return Marionette.Behavior.extend({
        defaults: {
            elements: null
        },

        initialize: function ()
        {
            this.isRegistered = false;
        },

        onShow: function ()
        {
            this.configureHead();
        },

        /**
         * Expose a receiver for triggerMethod('configure:head'). Can optionally
         * be called with a selector to only do the configuration for that element.
         *
         * @param selector
         */
        onConfigureHead: function (selector)
        {
            if (!selector)
            {
                this.configureHead();
                return;
            }

            if (!_.has(this.options.elements, selector))
            {
                throw new Error('Unspecified head configuration selector: "' + selector + '"');
            }

            this.configureHeadElement(this.options.elements[selector], selector);
        },

        onDestroy: function ()
        {
            this.constructor.deregister(this);
        },

        /**
         * Apply the configuration for all elements
         * @private
         */
        configureHead: function ()
        {
            _.each(this.options.elements, this.configureHeadElement, this);
        },

        /**
         * Apply the configuration for some specific element
         * @private
         * @param settings
         * @param selector
         */
        configureHeadElement: function (settings, selector)
        {
            // jshint eqnull:true

            if (!this.isRegistered)
                this.constructor.register(this);

            var elem = this.constructor.getElement(selector);

            if (settings.text)
            {
                var newText = this.getSettingValue(settings.text, elem);

                if (newText != null)
                    elem.text(newText);
            }

            if (settings.attributes)
            {
                _.each(settings.attributes, function (setting, attribute)
                {
                    var value = this.getSettingValue(setting, elem);

                    if (value != null)
                        elem.attr(attribute, value);
                }, this);
            }

            if (settings.styles)
            {
                _.each(settings.styles, function (setting, cssProp)
                {
                    var value = this.getSettingValue(setting, elem);

                    if (value != null)
                        elem.css(cssProp, value);
                }, this);
            }
        },

        getSettingValue: function (setting, elem)
        {
            return _.isFunction(setting) ? setting.call(this.view, elem) : setting;
        }
    }, {
        _registry: {},

        /**
         * Add all elements the instance wants to own to the registry, ensuring that they
         * are not already owned.
         *
         * @param instance
         */
        register: function (instance)
        {
            _.each(instance.options.elements, function (settings, selector)
            {
                // We naively assume that selectors and elements have a one-to-one mapping
                if (_.has(this._registry, selector))
                {
                    if (this._registry[selector].owner !== instance)
                        throw new Error('Conflicting head configuration for property "' + selector + '"');

                    return;
                }

                this._registry[selector] = {
                    owner: instance,
                    initial: this.getInitialValues(selector, settings)
                };
            }, this);

            instance.isRegistered = true;
        },

        /**
         * Get the initial values for all properties and attributes which will be modified
         *
         * @param selector
         * @param settings
         * @returns {{}}
         */
        getInitialValues: function (selector, settings)
        {
            var initial = {};

            var elem = this.getElement(selector);

            if (_.has(settings, 'text'))
                initial.text = elem.text();

            if (_.has(settings, 'attributes'))
            {
                initial.attributes = {};

                _.forEach(_.keys(settings.attributes), function (attribute)
                {
                    initial.attributes[attribute] = elem.attr(attribute);
                });
            }

            if (_.has(settings, 'styles'))
            {
                initial.styles = {};

                _.forEach(_.keys(settings.styles), function (cssProp)
                {
                    initial.styles[cssProp] = elem.css(cssProp);
                });
            }

            return initial;
        },

        /**
         * Remove all an instance's owned elements from the registry
         * @param instance
         */
        deregister: function (instance)
        {
            _.each(_.keys(instance.options.elements), function (selector)
            {
                if (!_.has(this._registry, selector) || this._registry[selector].owner !== instance)
                    throw new Error('Registry misconfiguration (selector "' + selector + '")');

                // Restore the initial values
                var elem = this.getElement(selector);

                var initial = this._registry[selector].initial;

                if (_.has(initial, 'text'))
                    elem.text(initial.text);

                if (_.has(initial, 'attributes'))
                    elem.attr(initial.attributes);

                if (_.has(initial, 'styles'))
                    elem.css(initial.styles);

                delete this._registry[selector];
            }, this);

            instance.isRegistered = false;
        },

        /**
         * Return the element specified by the selector, ensuring that the specifier gives a
         * unique value
         *
         * @param selector
         * @returns {jQuery}
         */
        getElement: function (selector)
        {
            var elem = $(selector);

            if (elem.length > 1)
                throw new Error('selector "' + selector + '" did not give a unique value');

            if (elem.length === 0)
                throw new Error('element "' + selector + '" not found');

            return elem;
        }
    });
});