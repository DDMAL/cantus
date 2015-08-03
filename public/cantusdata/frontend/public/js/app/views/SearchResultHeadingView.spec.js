"use strict";

describe('SearchResultHeadingView', function ()
{
    var testSetup = require('test/setup');

    var _ = require('underscore');
    var Backbone = require('backbone');

    var SearchResultHeadingView = require('views/SearchResultHeadingView');

    var getDummyMetadata = _.constant({query: 'abab'});

    var testResponse = {
        status: 200,
        contentType: 'application/json',
        responseText: JSON.stringify(['result 1', 'result numero dos'])
    };

    beforeEach(function ()
    {
        jasmine.Ajax.install();
        this.collection = new Backbone.Collection();

        this.init = function (opts)
        {
            opts = _.defaults(opts || {}, {
                collection: this.collection,
                getSearchMetadata: getDummyMetadata
            });

            this.view = new SearchResultHeadingView(opts);
            testSetup.showView(this.view);
        };
    });

    afterEach(function ()
    {
        testSetup.clearView();
        jasmine.Ajax.uninstall();
    });

    it('should throw an error if getSearchMetadata is not a function', function ()
    {
        expect(function ()
        {
            return new SearchResultHeadingView({
                getSearchMetadata: 'I am not a function'
            });
        }).toThrowError((/I am not a function/));
    });

    // Here I'm mostly just testing that the state and variables are what's expected;
    // I don't actually make sure that the right template gets rendered.

    it('should be in the NO_SEARCH state by default', function ()
    {
        this.init();
        expect(this.view.state).toBe(SearchResultHeadingView.states.NO_SEARCH);
    });

    it('should enter the SUCCESS state when a search completes', function ()
    {
        this.init();

        this.collection.fetch({url: 'http://example.org'});
        jasmine.Ajax.requests.mostRecent().respondWith(testResponse);

        expect(this.view.state).toBe(SearchResultHeadingView.states.SUCCESS);
    });

    it('should enter the FAILURE state when a search fails', function ()
    {
        this.init();

        this.collection.fetch({url: 'http://example.org'});
        jasmine.Ajax.requests.mostRecent().respondWith({
            status: 500,
            contentType: 'application/json',
            responseText: JSON.stringify({detail: 'That was bad'})
        });

        expect(this.view.state).toBe(SearchResultHeadingView.states.FAILURE);
    });

    it('should maintain state until a search resolves if showLoading is not truthy', function ()
    {
        this.init();
        this.collection.fetch({url: 'http://example.org'});

        expect(this.view.state).toBe(SearchResultHeadingView.states.NO_SEARCH);

        jasmine.Ajax.requests.mostRecent().respondWith(testResponse);

        expect(this.view.state).not.toBe(SearchResultHeadingView.states.NO_SEARCH);
    });

    it('should enter the LOADING state upon search request if showLoading is truthy', function ()
    {
        this.init({showLoading: true});
        this.collection.fetch({url: 'http://example.org'});

        expect(this.view.state).toBe(SearchResultHeadingView.states.LOADING);

        jasmine.Ajax.requests.mostRecent().respondWith(testResponse);

        expect(this.view.state).not.toBe(SearchResultHeadingView.states.LOADING);
    });

    // This is non-trivial because Marionette doesn't do it automatically
    it('should empty the view when the NO_SEARCH state is entered', function ()
    {
        this.init();
        this.view.setState(SearchResultHeadingView.states.SUCCESS);
        this.view.render();

        // Sanity check
        expect(this.view.$el).not.toBeEmpty();

        this.view.setState(SearchResultHeadingView.states.NO_SEARCH);
        this.view.render();

        expect(this.view.$el).toBeEmpty();
    });

    describe('setState', function ()
    {
        var values = function (view)
        {
            return _.pick(view, ['metadata', 'error', 'state']);
        };

        it('should throw an error on invalid state', function ()
        {
            this.init();

            var badFn = _.bind(this.view.setState, this.view, 'I am not a good state');
            expect(badFn).toThrowError((/I am not a good state/));
        });

        it('should set the metadata and error to null when the state is NO_SEARCH', function ()
        {
            this.init();

            this.view.error = 'foo';
            this.view.metadata = 'bar';

            this.view.setState(SearchResultHeadingView.states.NO_SEARCH);

            expect(values(this.view)).toEqual({
                state: SearchResultHeadingView.states.NO_SEARCH,
                metadata: null,
                error: null
            });
        });

        it('should set the metadata and null out the error when the state is SUCCESS', function ()
        {
            this.init();

            this.view.error = 'foo';
            this.view.metadata = 'bar';

            this.view.setState(SearchResultHeadingView.states.SUCCESS);

            // This uses getDummyMetadata
            expect(values(this.view)).toEqual({
                state: SearchResultHeadingView.states.SUCCESS,
                metadata: {query: 'abab'},
                error: null
            });
        });

        it('should set the metadata and null out the error when the state is LOADING', function ()
        {
            this.init();

            this.view.error = 'foo';
            this.view.metadata = 'bar';

            this.view.setState(SearchResultHeadingView.states.LOADING);

            // This uses getDummyMetadata
            expect(values(this.view)).toEqual({
                state: SearchResultHeadingView.states.LOADING,
                metadata: {query: 'abab'},
                error: null
            });
        });

        it('should set the error and null out the metadata when the state is FAILURE', function ()
        {
            this.init();

            this.view.error = 'foo';
            this.view.metadata = 'bar';

            var errResp = {status: 500};
            this.view.setState(SearchResultHeadingView.states.FAILURE, {error: errResp});

            // This uses getDummyMetadata
            expect(values(this.view)).toEqual({
                state: SearchResultHeadingView.states.FAILURE,
                metadata: null,
                error: errResp
            });
        });
    });

    describe('getErrorMessage', function ()
    {
        it('should give a generic message for 500 errors', function ()
        {
            this.init();
            expect(this.view.getErrorMessage({
                status: 500,
                responseJSON: {detail: 'Things went wrong'}
            })).toBe('The server encountered an error');
        });

        it('should use a JSON detail field if one is defined for 400 errors', function ()
        {
            this.init();

            expect(this.view.getErrorMessage({
                status: 422,
                responseJSON: {detail: 'Things went wrong'}
            })).toBe('Things went wrong');
        });

        it('should use a generic message for 400 errors if there is no detail field', function ()
        {
            this.init();

            var json = {fact: 'I have no detail field!'};
            var stringified = JSON.stringify(json);

            expect(this.view.getErrorMessage({
                status: 404,
                statusText: stringified,
                responseJSON: json
            })).toBe('The search could not be completed');
        });
    });

    describe('templateHelpers', function ()
    {
        it('should have fieldName, numFound and errorMessage set by default', function ()
        {
            this.init();

            expect(this.view.templateHelpers()).toEqual({
                fieldName: null,
                numFound: 0,
                errorMessage: null
            });
        });

        it('should use the values in view.metadata if it is given', function ()
        {
            this.init();

            this.view.metadata = {abc: 123, numFound: 9001};
            expect(this.view.templateHelpers()).toEqual({
                abc: 123,
                fieldName: null,
                numFound: 9001,
                errorMessage: null
            });
        });

        it('should derive errorMessage from view.error using view.getErrorMessage', function ()
        {
            this.init();

            var err = {}, msg = {};

            this.view.error = err;

            spyOn(this.view, 'getErrorMessage').and.returnValue(msg);

            expect(this.view.templateHelpers().errorMessage).toBe(msg);
            expect(this.view.getErrorMessage).toHaveBeenCalledWith(err);
        });
    });
});