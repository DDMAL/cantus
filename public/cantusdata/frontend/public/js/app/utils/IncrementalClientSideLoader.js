import _ from 'underscore';
import Marionette from 'marionette';

/**
 * Given an underlying Backbone collection, it incrementally copies its models
 * into another collection, proxying events from the underlying collection
 * into the new. This is a hackish way to support incrementally displaying
 * elements when a large collection has been loaded to the client side. Of
 * course, really the collection should just be paginated so that it can be
 * fetched incrementally.
 *
 * Its API is very similar to that of IncrementalSolrLoader.
 */
export default Marionette.Object.extend({
    rows: 20,

    /**
     * @param collection
     * @param underlyingCollection
     * @param {?dict} options Options for the loader. Available options:
     *   - rows: The number of rows to load per request
     * @constructor
     */
    constructor: function (collection, underlyingCollection, options)
    {
        this.collection = collection;
        this.underlyingCollection = underlyingCollection;
        this.options = options;

        this.initialize.apply(this, arguments);
    },

    initialize: function ()
    {
        this.mergeOptions(['rows']);

        this._initializeEventProxies();
    },

    /**
     * When a an event is triggered on the underlyingCollection, trigger the equivalent on the
     * collection
     * @private
     */
    _initializeEventProxies: function ()
    {
        _.forEach(['request', 'error'], function (event)
        {
            this.listenTo(this.underlyingCollection, event, function (underlying, requestInfo, options)
            {
                this.collection.trigger(event, this.collection, requestInfo, options);
            });
        }, this);

        this.listenTo(this.underlyingCollection, 'sync', this._syncCollection);

        this.listenTo(this.underlyingCollection, 'reset', function ()
        {
            this._copyElements('reset', 0);
        });
    },

    /**
     * Fetch results in the underlying collection
     * @param {?dict} options Fetch options
     */
    fetch: function (options)
    {
        return this.underlyingCollection.fetch(options);
    },

    /**
     * Load more models from the underlying collection into the collection, if there are
     * more models available.
     */
    continueLoading: function ()
    {
        if (this.collection.length < this.underlyingCollection.length)
        {
            this._copyElements('add', this.collection.length);
        }
    },

    /**
     * @param method The collection method to copy with
     * @param start The index at which to start the copy
     * @private
     */
    _copyElements: function (method, start)
    {
        var end = start + this.rows;

        var newModels = this.underlyingCollection.slice(start, end);
        this.collection[method](newModels);
    },

    /**
     * Reinitialize the collection with the initial elements of the
     * underlying collection and fake a sync event
     * @private
     */
    _syncCollection: function (underlying, requestInfo, options)
    {
        this._copyElements('reset', 0);
        this.collection.trigger('sync', this.collection, requestInfo, options);
    },

    /** Invalidate the current incremental load */
    stopLoading: function ()
    {
        this.underlyingCollection.reset();
    },

    /** @returns {Boolean} Return true if there are more results to load */
    hasMore: function ()
    {
        return this.underlyingCollection.length > this.collection.length;
    },

    /** @returns {Number} The number of results loaded */
    loaded: function ()
    {
        return this.collection.length;
    },

    /** @returns {Number} The number of results to load */
    numFound: function ()
    {
        return this.underlyingCollection.length;
    }
});
